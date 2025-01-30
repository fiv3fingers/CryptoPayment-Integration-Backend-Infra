
from src.utils.blockchain.types import UTXOTransferInfo, TransferInfo
from src.utils.currencies.types import CurrencyBase

def validate_transfer_info(transfer_info: TransferInfo, expected_amount: int, expected_currency: CurrencyBase, expected_sender: str, expected_deposit_address: str):
    if (
        transfer_info.amount < expected_amount
        or transfer_info.currency != expected_currency
        or transfer_info.source_address != expected_sender
        or transfer_info.destination_address != expected_deposit_address
    ):
        raise Exception("Invalid transaction hash: mismatched details")


def validate_utxo_transfer_info(transfer_info: UTXOTransferInfo, expected_amount: int, expected_currency: CurrencyBase, expected_sender: str, expected_deposit_address: str):
    found = False
    for out in transfer_info.outputs:
        if (
            out.destination_address == expected_deposit_address 
            and out.amount >= expected_amount 
            and transfer_info.currency == expected_currency 
            and transfer_info.source_address == expected_sender
        ):
            found = True
            break

    if not found:
        raise Exception("Invalid transaction hash: mismatched details")