from pydantic import BaseModel


class OrderRequest(BaseModel):
    order_id: int