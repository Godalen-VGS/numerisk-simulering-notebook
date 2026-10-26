"""Automatisk retting av 18-numerisk-simulering.

Hver sjekk i SJEKKER er én deltest, og poengene fordeles likt på dem.
De samme sjekkene ligger i "Test løsningen din"-cellen nederst i notebooken.
"""
import pytest

from notebook_loader import last_notebook

def naer(a, b, rel=1e-3):
    """Sant hvis tallet a er innenfor rel (relativt) av b."""
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) <= rel * abs(b)


def S(tekst):
    """Gjør tekst om til et sympy-uttrykk, f.eks. S("x**2 - 1")."""
    import sympy
    return sympy.sympify(tekst, locals={n: sympy.Symbol(n) for n in ("N", "O", "Q", "S")})


def lik(a, b):
    """Sant hvis a og b er matematisk like.

    Lister og mengder sammenlignes uten hensyn til rekkefølge, tupler (koordinater) i rekkefølge.
    """
    import sympy
    if a is None:
        return False
    if isinstance(b, tuple):
        if not isinstance(a, (tuple, list, sympy.Tuple)) or len(a) != len(b):
            return False
        return all(lik(x, y) for x, y in zip(a, b))
    if isinstance(b, (list, set)):
        if isinstance(a, sympy.FiniteSet):
            a = list(a)
        if not isinstance(a, (list, tuple, set)) or len(a) != len(b):
            return False
        rest = list(a)
        for y in b:
            for i, x in enumerate(rest):
                if lik(x, y):
                    del rest[i]
                    break
            else:
                return False
        return True
    if isinstance(b, dict):
        if not isinstance(a, dict) or len(a) != len(b):
            return False
        a = {str(k): v for k, v in a.items()}
        return all(str(k) in a and lik(a[str(k)], v) for k, v in b.items())
    try:
        a, b = sympy.sympify(a), sympy.sympify(b)
    except (sympy.SympifyError, TypeError):
        return False
    vanlige = lambda u: u.subs({s: sympy.Symbol(s.name) for s in u.free_symbols})
    a, b = vanlige(a), vanlige(b)
    if isinstance(a, sympy.Set) or isinstance(b, sympy.Set):
        return a == b
    if getattr(b, "is_Relational", False):
        return a == b
    try:
        return sympy.simplify(a - b) == 0
    except TypeError:
        return a == b

oppgave = last_notebook("oppgave")

SJEKKER = [
    ('1_lengde', 'euler(f, 0, 1, 0.1, 10) skal gi lister med 11 elementer', 'len(euler(lambda t, y: y, 0, 1, 0.1, 10)[0]) == 11 and len(euler(lambda t, y: y, 0, 1, 0.1, 10)[1]) == 11'),
    ('1_verdi', "euler for y' = y med h = 0.1 og n = 10 skal gi siste verdi 1.1^10 ≈ 2.594", 'naer(euler(lambda t, y: y, 0, 1, 0.1, 10)[1][-1], 1.1**10, rel=1e-9)'),
    ('1_tid', 'siste tid fra euler(f, 2, 0, 0.5, 4) skal være 4.0', 'naer(euler(lambda t, y: 1, 2, 0, 0.5, 4)[0][-1], 4)'),
    ('1_avhenger_av_t', "euler skal sende tiden inn i f: y' = 2t fra 0 med h = 0.5, n = 2 gir 0.5", 'naer(euler(lambda t, y: 2*t, 0, 0, 0.5, 2)[1][-1], 0.5, rel=1e-9)'),
    ('2', 'avkjoling(90, 20, 0.05, 0.5, 60) skal gi temperaturen etter 60 min med Euler', 'naer(avkjoling(90, 20, 0.05, 0.5, 60), 20 + 70*(1 - 0.05*0.5)**120, rel=1e-6)'),
    ('3_01', 'feil_euler(0.1) skal gi ca. 0.1245', 'naer(feil_euler(0.1), 2.718281828459045 - 1.1**10, rel=1e-6)'),
    ('3_001', 'feil_euler(0.001) skal gi ca. 0.00136', 'naer(feil_euler(0.001), 2.718281828459045 - 1.001**1000, rel=1e-6)'),
]


@pytest.mark.parametrize(
    "beskrivelse,uttrykk", [s[1:] for s in SJEKKER], ids=[s[0] for s in SJEKKER]
)
def test_sjekk(beskrivelse, uttrykk):
    navnerom = {**vars(oppgave), "naer": naer, "lik": lik, "S": S}
    assert eval(uttrykk, navnerom), beskrivelse
