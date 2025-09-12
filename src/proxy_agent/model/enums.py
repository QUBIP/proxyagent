

import logging
from enum import StrEnum

log = logging.getLogger(__name__)

class PqcAlgorithm(StrEnum):
    BIKE_L1 = "BIKE-L1"
    BIKE_L3 = "BIKE-L3"
    BIKE_L5 = "BIKE-L5"

    MCELIECE348864 ="Classic-McEliece-348864"
    MCELIECE460896 ="Classic-McEliece-460896"
    MCELIECE6688128 ="Classic-McEliece-6688128"
    MCELIECE6960119 ="Classic-McEliece-6960119"
    MCELIECE8192128 ="Classic-McEliece-8192128"

    MCELIECE348864_F ="Classic-McEliece-348864f"
    MCELIECE460896_F ="Classic-McEliece-460896f"
    MCELIECE6688128_F ="Classic-McEliece-6688128f"
    MCELIECE6960119_F ="Classic-McEliece-6960119f"
    MCELIECE8192128_F ="Classic-McEliece-8192128f"

    HQC_128 = "HQC-128"
    HQC_192 = "HQC-192"
    HQC_256 = "HQC-256"

    KYBER512 = "Kyber512"
    KYBER768 = "Kyber768"
    KYBER1024 = "Kyber1024"
    
    ML_KEM512 = "ML-KEM-512"
    ML_KEM768 = "ML-KEM-768"
    ML_KEM1024 =  "ML-KEM-1024"

    SNTRUP761 = "sntrup761"

    FRODO_KEM_640_AES = "FrodoKEM-640-AES"
    FRODO_KEM_976_AES = "FrodoKEM-976-AES"
    FRODO_KEM_1344_AES = "FrodoKEM-1344-AES"

    FRODO_KEM_640_SHAKE = "FrodoKEM-640-SHAKE"
    FRODO_KEM_976_SHAKE = "FrodoKEM-976-SHAKE"
    FRODO_KEM_1344_SHAKE = "FrodoKEM-1344-SHAKE"

    @classmethod
    def parse_from_string(cls, input_string: str) -> StrEnum:

        try:
            return cls(input_string)
        except ValueError:
            log.info("Could not directly parse %s, checking other posible names for the algorithms", input_string)

        if input_string == "kyber":
            log.info("Found that 'kyber' is an alias of %s", cls.KYBER512)
            return cls.KYBER512

        log.error("Proxy agent could not parse %s into any algorithm, defaulting in Kyber512", input_string)
        return cls.KYBER512


class HybridizationMethod(StrEnum):
    XORING = "xoring"
    HMAC = "hmac"
    XORMAC = "xormac"

    @classmethod
    def parse_from_string(cls, input_string: str) -> StrEnum:

        try:
            return cls(input_string)
        except ValueError:
            log.info("Could not directly parse %s, checking other posible names for the algorithms", input_string)

        if input_string == "xor":
            log.info("Found that 'xor' is an alias of %s", cls.XORING)
            return cls.XORING

        log.error("Proxy agent could not parse %s into any algorithm, defaulting in Kyber512", input_string)
        return cls.XORING