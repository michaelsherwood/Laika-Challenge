from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from service import ShotgridQuery

app = FastAPI()

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")


# Get data from Shotgrid
def get_sg_query() -> list:
    sg = ShotgridQuery()

    entity_type = "Sequence"
    filters = [["project", "is", {"type": "Project", "id": 85}]]
    fields = ["code", "sg_cut_duration", "sg_ip_versions"]

    data = sg.get_data(entity_type, filters, fields)

    return data


# Home page
@app.get("/")
async def index(request: Request):
    # data = get_sg_query()
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/data")
async def get_data():
    data = get_sg_query()
    return JSONResponse(content=data)
