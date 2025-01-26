from pydantic import BaseModel, ConfigDict


class BaseRequest(BaseModel):
    """Base model for all exchange requests"""

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        alias_generator=lambda x: "".join(
            word.capitalize() if i else word for i, word in enumerate(x.split("_"))
        ),
    )


class QUOTERequest(BaseRequest):
    """Exchange estimation request"""

    from_currency: str
    to_currency: str
    from_network: str
    amount: float

    def to_api_params(self) -> dict:
        """Convert to API parameters"""
        params = self.model_dump(by_alias=True, exclude_none=True)

        # Format amounts to 8 decimal places if present
        if self.amount is not None:
            params["amount"] = f"{self.amount:.8f}"

        return params
