import pytest

from app.pipeline.normalize import mask_pii, normalize


@pytest.mark.parametrize(
    ("raw", "masked"),
    [
        ("hubungi aku di budi.s@gmail.com ya", "hubungi aku di [EMAIL] ya"),
        ("wa aku 0812-3456-7890", "wa aku [NOMOR]"),
        ("nomorku +62 812 3456 7890", "nomorku [NOMOR]"),
        ("NIK 3374012345678901", "NIK [NIK]"),
        ("rumahku jl. Merpati Raya no 12A", "rumahku [ALAMAT]"),
        ("di rt 03 / rw 05", "di [ALAMAT]"),
        ("aku capek banget hari ini", "aku capek banget hari ini"),
    ],
)
def test_mask_pii(raw: str, masked: str) -> None:
    assert mask_pii(raw) == masked


@pytest.mark.parametrize(
    ("raw", "canonical"),
    [
        ("Akuuu pgn m4ti ajaaa", "aku ingin mati saja"),  # huruf berulang, slang, leet
        ("b*nuh d*ri", "bunuh diri"),  # sensor
        ("wis ora kuat urip", "sudah tidak kuat hidup"),  # Jawa
        ("pengen ⚰️", "ingin mati"),  # emoji
        ("mau gantng diri", "mau gantung diri"),  # salah ketik kata kunci
        ("teman2 ku", "teman teman aku"),  # reduplikasi angka 2
        ("gue gak tau", "aku tidak tau"),
    ],
)
def test_canonical_tokens(raw: str, canonical: str) -> None:
    assert normalize(raw).text == canonical


def test_fuzzy_correction_only_targets_crisis_keywords() -> None:
    # kata biasa ≥ 5 huruf tidak boleh "dikoreksi" jadi kata lain
    assert normalize("sekolah besok").text == "sekolah besok"


def test_original_text_is_kept() -> None:
    n = normalize("Aku SEDIH 😭")
    assert n.original == "Aku SEDIH 😭" and "emo_nangis" in n.tokens
