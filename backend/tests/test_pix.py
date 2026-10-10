from types import SimpleNamespace

from pixactions_api.pix.brcode import build_brcode, crc16_ccitt
from pixactions_api.pix.mock import MockPixProvider
from pixactions_api.timeutil import utcnow


def test_crc16_ccitt_known_vector():
    assert crc16_ccitt("123456789") == "29B1"


def test_brcode_structure_and_crc():
    code = build_brcode(
        pix_key="SANDBOX-NAO-PAGUE", amount_brl_cents=2000,
        merchant_name="PIX ACTIONS SANDBOX", merchant_city="SAO PAULO", txid="MOCKABC123",
    )
    assert code.startswith("000201")
    assert "0014br.gov.bcb.pix" in code
    assert "540520.00" in code
    assert "5303986" in code and "5802BR" in code
    assert code[-8:-4] == "6304"
    assert code[-4:] == crc16_ccitt(code[:-4])


async def test_mock_charge_and_payment(settings):
    pix = MockPixProvider(settings)
    charge = await pix.create_charge(order_id="0a1b2c3d-0000-0000-0000-000000000000", amount_brl_cents=2000, description="x")
    assert charge.charge_id.startswith("MOCK") and len(charge.charge_id) <= 25
    assert charge.expires_at > utcnow()
    unpaid = SimpleNamespace(created_at=utcnow(), pix_paid_at=None)
    assert await pix.is_paid(unpaid) is False
    assert await pix.is_paid(SimpleNamespace(created_at=utcnow(), pix_paid_at=utcnow())) is True


async def test_sandbox_pix_key_cannot_receive_real_payments(settings):
    """The sandbox BR Code must not carry a key a real person could register (email/phone/CPF/random key)."""
    pix = MockPixProvider(settings)
    charge = await pix.create_charge(order_id="0a1b2c3d-0000-0000-0000-000000000000", amount_brl_cents=500, description="x")
    gui = "0014br.gov.bcb.pix"
    key_field = charge.brcode[charge.brcode.index(gui) + len(gui):]
    key = key_field[4 : 4 + int(key_field[2:4])]
    assert key == "SANDBOX-NAO-PAGUE"
    assert "@" not in key and not key.replace("-", "").isdigit()
