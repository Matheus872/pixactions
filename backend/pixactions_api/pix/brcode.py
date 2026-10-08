"""EMV 'copia e cola' payload (BR Code) for static-format Pix charges."""


def _tlv(tag: str, value: str) -> str:
    return f"{tag}{len(value):02d}{value}"


def crc16_ccitt(data: str) -> str:
    crc = 0xFFFF
    for byte in data.encode():
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
            crc &= 0xFFFF
    return f"{crc:04X}"


def build_brcode(
    *, pix_key: str, amount_brl_cents: int, merchant_name: str, merchant_city: str, txid: str
) -> str:
    amount = f"{amount_brl_cents // 100}.{amount_brl_cents % 100:02d}"
    account = _tlv("00", "br.gov.bcb.pix") + _tlv("01", pix_key)
    payload = (
        _tlv("00", "01")
        + _tlv("26", account)
        + _tlv("52", "0000")
        + _tlv("53", "986")
        + _tlv("54", amount)
        + _tlv("58", "BR")
        + _tlv("59", merchant_name[:25])
        + _tlv("60", merchant_city[:15])
        + _tlv("62", _tlv("05", txid[:25]))
        + "6304"
    )
    return payload + crc16_ccitt(payload)
