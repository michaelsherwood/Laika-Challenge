import os

from shotgun_api3 import Shotgun
from dotenv import load_dotenv

# dev imports
import json  # NOTE Remove for production
import time  # NOTE Remove for production

# Load credentials from .env file
load_dotenv()


class ShotgridQuery:
    def __init__(
            self,
            project_id: int = 85,
            entity_type: str = "Sequence",
            query_fields: list = ["sg_cut_duration", "sg_ip_versions"]
        ) -> None:
        self.project_id = project_id
        self.entity_type = entity_type
        self.query_fields = query_fields


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


    def __get_query_field_schema(self, schema: dict, fields: list = []) -> list:
        """Get the query fields from the schema for an entity type.

        Args:
            schema (dict): The entity type schema
            fields (list, optional): A list of query fields to search for

        Returns:
            list: The query fields detected in a schema
        """
        # Define a list to store the query fields
        query_fields = []

        # Loop through the schema and get the query fields
        for field_name, field_metadata in schema.items():

            # Skip fields that are not in the fields list
            # this is used to filter out built-in ShotGrid query fields
            if fields and field_name not in fields:
                continue

            # Check if the field has a query property
            if field_metadata.get("properties") and field_metadata["properties"].get("query"):

                # Get the properties metadata
                properties_metadata = field_metadata["properties"]

                # Declare variables to store in the query fields list
                _field_data_type = field_metadata.get("data_type", {}).get("value")
                _entity_type = field_metadata.get("entity_type", {}).get("value")

                _summary_default = properties_metadata.get("summary_default", {}).get("value")
                _summary_field = properties_metadata.get("summary_field", {}).get("value")
                _query = properties_metadata.get("query", {}).get("value")

                # Create a dictionary to store the query field
                _query_field = {
                    "field": field_name,
                    "field_data_type": _field_data_type,
                    "entity_type": _entity_type,
                    "summary_default": _summary_default,
                    "summary_field": _summary_field,
                    "query": _query,
                }

                # Append the query field to the query fields list
                query_fields.append(_query_field)

        return query_fields


    def __get_sequences(self, sg: Shotgun, project_id: int) -> list:
        """Get all sequences for a project.

        Args:
            sg (Shotgun): An instance of the Shotgrid API
            project_id (int): The ID of the project to get sequences for

        Returns:
            list: A list of sequences for the project
        """
        filters = [["project", "is", {"type": "Project", "id": project_id}]]
        fields = ["sg_cut_duration", "sg_ip_versions", "code"]

        sequences = sg.find(entity_type="Sequence", filters=filters, fields=fields)

        return sequences
