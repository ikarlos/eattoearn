import uuid
from phonepe.sdk.pg.payments.v1.models.request.pg_pay_request import PgPayRequest
from phonepe.sdk.pg.payments.v1.payment_client import PhonePePaymentClient
from phonepe.sdk.pg.env import Env
from phonepe.sdk.pg.payments.v1.models.response.phonepe_response import PhonePeResponse

from Env.settings import Settings


class PhonePeClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._merchant_id = settings.merchant_id
        self._salt_key = settings.salt_key
        self._salt_index = settings.salt_index
        self._env = Env.UAT
        self._phonepe_client = PhonePePaymentClient(
            merchant_id=self._merchant_id,
            salt_key=self._salt_key,
            salt_index=self._salt_index,
            env=self._env,
        )

    #
    def init_payment(self, amount: int = 1, user_uid: str = "") -> PhonePeResponse:
        unique_transaction_id = str(uuid.uuid4())[:-2]
        ui_redirect_url = self.settings.ui_redirect_url
        s2s_callback_url = self.settings.s2s_callback_url
        id_assigned_to_user_by_merchant = user_uid
        #
        pay_page_request = PgPayRequest.pay_page_pay_request_builder(
            merchant_transaction_id=unique_transaction_id,
            amount=amount * 100,
            merchant_user_id=id_assigned_to_user_by_merchant,
            callback_url=s2s_callback_url,
            redirect_url=ui_redirect_url,
        )
        #
        pay_page_response: PhonePeResponse = self._phonepe_client.pay(pay_page_request)
        return pay_page_response

    def check_status(self, merchant_transaction_id: str):
        response = self._phonepe_client.check_status(merchant_transaction_id)
        return response
