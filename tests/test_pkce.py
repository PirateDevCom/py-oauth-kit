import re

from py_oauth.pkce import code_challenge, generate_code_verifier


def test_code_verifier_format():
    verifier = generate_code_verifier()
    # RFC 7636 §4.1: 43-128 unreserved characters.
    assert re.fullmatch(r"[A-Za-z0-9\-._~]{43,128}", verifier)


def test_code_verifier_is_random():
    assert generate_code_verifier() != generate_code_verifier()


def test_code_challenge_rfc_example():
    # RFC 7636 Appendix B.
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    assert code_challenge(verifier) == "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
