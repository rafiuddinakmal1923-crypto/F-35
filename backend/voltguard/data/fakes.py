"""Fake personal details for the restricted customer_pii table (R0 only).

Every name starts with "FAKE" so a screenshot can never be mistaken for real customer data.
"""

from __future__ import annotations

import numpy as np

MALAY_GIVEN_M = ["Ahmad", "Hafiz", "Faizal", "Azman", "Rizal", "Syafiq", "Amirul", "Khairul"]
MALAY_GIVEN_F = ["Siti", "Nurul", "Aishah", "Farah", "Zarina", "Hidayah", "Nadia", "Salmah"]
MALAY_FATHER = ["Ali", "Rahman", "Ismail", "Yusof", "Hassan", "Osman", "Abdullah", "Hamid"]
CHINESE = ["Tan Wei Ming", "Lim Mei Ling", "Wong Kok Leong", "Lee Siew Lan", "Ng Chee Keong", "Chong Pei Shan"]
INDIAN_GIVEN_M = ["Kumar", "Suresh", "Rajesh", "Ganesh", "Vijay"]
INDIAN_GIVEN_F = ["Priya", "Kavitha", "Lakshmi", "Devi", "Shanthi"]
INDIAN_FATHER = ["Muthu", "Raman", "Subramaniam", "Krishnan", "Arumugam"]
STREET_WORDS = ["Mawar", "Melati", "Cempaka", "Kenanga", "Seroja", "Dahlia", "Orkid", "Teratai"]
TAMAN = ["Taman Seri Indah", "Taman Desa Damai", "Taman Bukit Jaya", "Taman Sri Murni"]
TOWNS = {
    "CEN": [("47000", "Sungai Buloh", "Selangor"), ("47301", "Petaling Jaya", "Selangor")],
    "NOR": [("11900", "Bayan Lepas", "Pulau Pinang"), ("13700", "Seberang Jaya", "Pulau Pinang")],
}


def fake_name(rng: np.random.Generator) -> str:
    group = rng.integers(0, 3)
    female = rng.random() < 0.5
    if group == 0:
        given = rng.choice(MALAY_GIVEN_F if female else MALAY_GIVEN_M)
        return f"FAKE {given} {'binti' if female else 'bin'} {rng.choice(MALAY_FATHER)}"
    if group == 1:
        return f"FAKE {rng.choice(CHINESE)}"
    given = rng.choice(INDIAN_GIVEN_F if female else INDIAN_GIVEN_M)
    return f"FAKE {given} {'a/p' if female else 'a/l'} {rng.choice(INDIAN_FATHER)}"


def fake_address(rng: np.random.Generator, region: str, house_no: int, street_no: int) -> str:
    postcode, town, state = TOWNS.get(region, TOWNS["CEN"])[int(rng.integers(0, 2))]
    street = STREET_WORDS[street_no % len(STREET_WORDS)]
    taman = TAMAN[street_no % len(TAMAN)]
    return f"No. {house_no}, Jalan {street} {street_no % 9 + 1}, {taman}, {postcode} {town}, {state}"


def fake_phone(rng: np.random.Generator) -> str:
    return f"01{rng.integers(0, 10)}-{rng.integers(100, 1000)} {rng.integers(1000, 10000)}"


def fake_ic(rng: np.random.Generator, dashes: bool = True) -> str:
    yy, mm, dd = rng.integers(60, 99), rng.integers(1, 13), rng.integers(1, 29)
    birth = f"{yy:02d}{mm:02d}{dd:02d}"
    place, serial = f"{rng.integers(1, 15):02d}", f"{rng.integers(1000, 10000)}"
    return f"{birth}-{place}-{serial}" if dashes else f"{birth}{place}{serial}"
