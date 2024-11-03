import os

from shotgun_api3 import Shotgun
from dotenv import load_dotenv

# dev imports
import json  # NOTE Remove for production
import time  # NOTE Remove for production

# Load credentials from .env file
load_dotenv()


def get_shotgrid_connection():
    """
    Get a connection to Shotgrid using the credentials in the environment variables

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


def get_schema(sg: Shotgun, entity_type: str):
    """
    Get the schema for an entity type

    Args:
        sg (Shotgun): An instance of the Shotgrid API
        entity_type (str): The name of the entity type to get the schema for

    Returns:
        dict: The schema for the entity type
    """
    schema = sg.schema_field_read(entity_type)

    return schema


def get_sequences(sg: Shotgun, project_id: int):
    """
    Get all sequences for a project

    Args:
        sg (Shotgun): An instance of the Shotgrid API
        project_id (int): The ID of the project to get sequences for

    Returns:
        list: A list of sequences with the fields "sg_cut_duration", "sg_ip_versions", and "code"
    """
    filters = [["project", "is", {"type": "Project", "id": project_id}]]
    fields = ["sg_cut_duration", "sg_ip_versions", "code"]

    sequences = sg.find(entity_type="Sequence", filters=filters, fields=fields)

    return sequences


if __name__ == "__main__":
    project_id = 85

    st = time.time()  # NOTE Remove for production
    sg = get_shotgrid_connection()

    print(f"Connection time: {(time.time() - st) * 1000:.0f}ms")  # NOTE Remove for production

    st = time.time()
    schema = get_schema(sg, "Sequence")

    print(f"Schema time: {(time.time() - st) * 1000:.0f}ms")
    with open("data/schema.json", "w") as f:
        json.dump(schema, f, indent=2, default=str)

    st = time.time()  # NOTE Remove for production
    sequences = get_sequences(sg, project_id)

    # NOTE Remove for production
    print(f"Sequences time: {(time.time() - st) * 1000:.0f}ms")   
    with open("data/sequences.json", "w") as f:
        json.dump(sequences, f, indent=2, default=str)