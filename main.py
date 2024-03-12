from typing import Union

from fastapi import FastAPI

import uvicorn

app = FastAPI()

todos = [{
    "id":1,
    "name":"pakorn"
    },
    {
    "id":2,
    "name":"boonkamse"
    }
]

@app.get("/hello")
def read_root(name:str,surname:str):
    return {"Hello": "World","name":name,"surename":surname}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

# demostrate get method
@app.get("/test_todo",tags=['root'])
async def root()->dict:
    return {"ping":"pong"}

#get read todo
@app.get("/test_todo_2",tags=['Todos'])
async def get_todos()->dict:
    return {"data":todos}

todo = {"hello":"test"}
# demostrate post method
@app.post('/test_todo_2',tags=["Todos"])
async def add_todos(todo:dict)->dict:
    todos.append(todo)
    return {"data_send_done":"done"}

# demostrate put method
@app.put('/test_todo_2/{id}',tags=["Todos"])
async def update_todos(id:int,body:dict)->dict:
    for todo in todos:
        if (int(todo[int])) == id:
            pass



if __name__ == '__main__':
    uvicorn.run("main:app",host="127.0.0.1",port=8000,log_level='info')