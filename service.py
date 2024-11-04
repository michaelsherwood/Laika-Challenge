"""Service module for interacting with Shotgrid."""

import os

from shotgun_api3 import Shotgun
from dotenv import load_dotenv
from typing import Any

# Load credentials from .env file
load_dotenv()


class ShotgridQuery:
    def __init__(
        self, entity_type: str = "", filters: list = [], fields: list = []
    ) -> None:
        self.entity_type = entity_type
        self.filters = filters
        self.fields = fields

    def create_shotgrid_connection(self) -> Shotgun:
        """Create a connection to Shotgrid.

        Returns:
            Shotgun: An instance of the Shotgrid API
        """
        # Get Shotgrid credentials from environment variables
        shotgrid_url = os.getenv("SG_HOST")
        shotgrid_script_name = os.getenv("SG_SCRIPT_NAME")
        shotgrid_script_key = os.getenv("SG_SCRIPT_KEY")

        # Create a shotgrid connection
        sg = Shotgun(shotgrid_url, shotgrid_script_name, shotgrid_script_key)

        return sg

    def get_data(self, entity_type: str, filters: list = [], fields: list = []) -> dict:
        """Get entity data including query fields from Shotgrid.

        Args:
            entity_type (str): The name of the entity type to get data for
            filters (list, optional): A list of filters to apply to the query. Defaults to [].
            fields (list, optional): A list of fields to return in the query. Defaults to [].

        Returns:
            dict: A dictionary of data from Shotgrid
        """
        self.entity_type = entity_type
        self.filters = filters
        self.fields = fields

        sg = self.create_shotgrid_connection()

        # Get entities from SG
        entities = self.__get_entities(sg, self.entity_type, self.filters, self.fields)

        # Exit early if no entities are found
        if not entities:
            return []

        # Get schema for entity type
        schema = self.__get_schema(sg, self.entity_type)

        # Filter out query fields that are not in self.fields
        query_fields = {}

        for field_name, field_metadata in schema.items():
            if (
                "query" in field_metadata.get("properties", {})
                and field_name in self.fields
            ):
                query_fields[field_name] = schema[field_name]

        # Populate query fields if they exist
        if query_fields:
            updated_entities = []

            for entity in entities:
                updated_entity = self.__populate_query_fields(sg, entity, query_fields)
                updated_entities.append(updated_entity)

            return updated_entities

        sg.close()
        return entities

    def __get_entities(
        self, sg: Shotgun, entity_type: str, filters: list = [], fields: list = []
    ) -> list:
        """Get all entities for a project.

        Args:
            sg (Shotgun): An instance of the Shotgrid API
            entity_type (str): The name of the entity type to get entities for
            filters (list, optional): A list of filters to apply to the query. Defaults to [].
            fields (list, optional): A list of fields to return in the query. Defaults to [].

        Returns:
            list: A list of entities for the project
        """
        entities = sg.find(entity_type=entity_type, filters=filters, fields=fields)

        return entities

    def __get_schema(self, sg: Shotgun, entity_type: str) -> dict:
        """Get the schema for an entity type.

        Args:
            sg (Shotgun): An instance of the Shotgrid API
            entity_type (str): The name of the entity type to get the schema for

        Returns:
            dict: The schema for the entity type
        """
        # Get the schema for the entity type
        schema = sg.schema_field_read(entity_type)

        return schema

    def __populate_query_fields(
        self, sg: Shotgun, entity: dict, query_fields: dict
    ) -> dict:
        """Populate query fields for an entity.

        Args:
            sg (Shotgun): An instance of the Shotgrid API
            entity (dict): The entity to populate query fields for
            query_fields (dict): A dictionary of query fields to populate

        Returns:
            dict: The entity with populated query fields
        """
        for field_name, field_metadata in query_fields.items():
            query_field = QueryField(sg, field_name, field_metadata, entity)
            query_field_data = query_field.get_query_data()

            entity[field_name] = query_field_data
        return entity


class QueryField:
    def __init__(
        self, sg: Shotgun, field_name: str, field_metadata: dict, entity: dict = None
    ):
        self.sg = sg
        self.field_name = field_name
        self.field_metadata = field_metadata
        self.parent_entity = self.__get_parent_entity(entity)

        self.properties = field_metadata.get("properties")

        self.summary_default = self.properties.get("summary_default", {}).get("value")
        self.summary_value = self.properties.get("summary_value", {}).get("value")
        self.summary_field = self.properties.get("summary_field", {}).get("value")

        self.query = self.properties.get("query", {}).get("value")

        self.filters = self.query.get("filters")
        self.entity_type = self.query.get("entity_type")

    def get_query_data(self) -> Any:
        """Retrieve query data based on the summary default value.

        Depending on the value of `self.summary_default`, this method will:
        - Perform a query calculation for "average", "count", "maximum", "minimum", or "sum".
        - Perform a record count query for "record_count".
        - Perform a single record query for "single_record".
        - Raise a ValueError for any other value.

        Returns:
            Any: The result of the query based on the summary default value.

        Raises:
            ValueError: If the summary default value is not supported.
        """
        if self.summary_default in [
            "average",
            "count",
            "maximum",
            "minimum",
            "sum",
        ]:
            return self.query_calculation(calculation_type=self.summary_default)
        elif self.summary_default == "record_count":
            return self.query_record_count()
        elif self.summary_default == "single_record":
            return self.query_single_record()
        else:
            raise ValueError(f"Summary Default {self.summary_default} not supported.")

    def get_sg_filters(self) -> list:
        """Convert query field conditions to Shotgrid filters.

        Returns:
            list: A list of Shotgrid filters
        """
        conditions = self.filters
        filters = self.__convert_conditions_to_filter(conditions)

        return [filters]

    def query_calculation(self, calculation_type: str) -> Any:
        """Perform a query calculation on the Shotgrid entity.

        Args:
            calculation_type (str): The type of calculation to perform. Supported values are:
                - "average"
                - "count"
                - "maximum"
                - "minimum"
                - "sum"

        Returns:
            Any: The result of the query calculation.
        """
        filters = self.get_sg_filters()
        field = self.summary_field
        summary_fields = [{"field": field, "type": calculation_type}]

        summary = self.sg.summarize(
            entity_type=self.entity_type, filters=filters, summary_fields=summary_fields
        )

        return summary["summaries"][field]

    def query_record_count(self) -> int:
        """Perform a record count query on the Shotgrid entity.

        Returns:
            int: The number of records returned by the query.
        """
        filters = self.get_sg_filters()
        field = self.summary_field
        summary_fields = [{"field": field, "type": "count"}]

        summary = self.sg.summarize(
            entity_type=self.entity_type, filters=filters, summary_fields=summary_fields
        )

        return summary["summaries"][field]

    def query_single_record(self) -> str:
        """Perform a single record query on the Shotgrid entity.

        Returns:
            str: The result of the query.
        """
        filters = self.get_sg_filters()
        field = self.summary_field

        sg_results = self.sg.find(
            entity_type=self.entity_type, filters=filters, fields=[field]
        )

        if not sg_results:
            return None

        results = []
        for entity in sg_results:
            if isinstance(entity.get(field), dict):
                results.append(entity[field].get("name"))
            else:
                results.append(entity[field])

        return ", ".join(results)

    def logical_operator_lookup(self, operator: str) -> str:
        """Lookup table for logical operators.

        Args:
            operator (str): The logical operator to lookup.

        Returns:
            str: The Shotgrid logical operator.
        """
        operator_lookup = {"and": "all", "or": "any"}
        if operator in operator_lookup.keys():
            return operator_lookup[operator]
        raise ValueError(f"Logical Operator {operator} not found in lookup.")

    def __convert_conditions_to_filter(self, conditions: list) -> list:
        """Convert conditions to Shotgrid filters.

        Args:
            conditions (list): A list of conditions to convert to filters.

        Returns:
            list: A list of Shotgrid filters.
        """
        sg_filters = []

        logical_operator = self.logical_operator_lookup(
            conditions.get("logical_operator")
        )

        for condition in conditions.get("conditions", []):
            if "conditions" in condition.keys():
                # Recursively convert conditions subgroup to filter
                nested_filters = self.__convert_conditions_to_filter(condition)

                # Append the nested filter group
                sg_filters.append(nested_filters)
            else:
                # Process condition
                active = condition.get("active", True)
                path = condition.get("path")
                relation = condition.get("relation")
                values = condition.get("values", [])

                if not active:
                    continue

                # Check if value needs to be replaced with parent_entity
                lookup_values = []
                for value in values:
                    if (
                        isinstance(value, dict)
                        and value.get("valid") == "parent_entity_token"
                    ):
                        lookup_values.append(self.parent_entity)
                    else:
                        lookup_values.append(value)

                # Use single value if only one value is present
                value = lookup_values
                if len(lookup_values) == 1:
                    value = lookup_values[0]

                sg_filters.append([path, relation, value])

        return {"filter_operator": logical_operator, "filters": sg_filters}

    def __get_parent_entity(self, entity: dict) -> dict:
        """Get the parent entity from the entity dictionary.

        Args:
            entity (dict): The entity to get the parent entity from.

        Returns:
            dict: The parent entity dictionary.
        """
        keys = ["type", "id"]
        parent_entity = {}

        for key in keys:
            parent_entity[key] = entity.get(key, None)

        return parent_entity


if __name__ == "__main__":
    filters = [["project", "is", {"type": "Project", "id": 85}]]
    fields = ["code", "sg_cut_duration", "sg_ip_versions"]

    sg_query = ShotgridQuery()
    sequences = sg_query.get_data(
        entity_type="Sequence", filters=filters, fields=fields
    )
