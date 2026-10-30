"""Hardened derivative of the supplied standard-library feasibility consumer.

The arithmetic/geometry kernel is copied from exact_checker.py. Added validation
requires the declared schema, exact decimal STRING geometry, and strict integer
counts/indices. JSON duplicate keys and nonfinite constants are rejected. Output
grid endpoints are formatted exactly using integers, with no Decimal rounding.
See checker_audit.md for the audit, scope, and rationale. Originals are preserved.

The certificate defines genuine regular polygons by exact rational centers/radii
and exact rational angles (in radians). Rational separating vectors are witnesses.
Every elementary operation encloses its result on the fixed rational grid 10^-60.
Pi is enclosed using Machin's identity and alternating arctangent series; sin/cos
use Taylor's theorem with a rational Lagrange remainder. There are NO floating
point decisions, geometric tolerances, solver imports, or empirical error bounds.

This verifies one construction, never global optimality. Read CHECKER_NOTES.md.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from math import factorial
from pathlib import Path
from decimal import Decimal
import argparse, json, re

D = 10**60
SCHEMA = 'regular-polygon-separation-v1'
DECIMAL_STRING = re.compile(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z')


def _decimal_scalar(value, label):
    # Do not let Fraction(float) silently change the written decimal geometry.
    if type(value) is not str or DECIMAL_STRING.fullmatch(value) is None:
        raise ValueError(f'{label} must be a finite exact decimal string')


def validate_certificate(cert, expected=None):
    if type(cert) is not dict:
        raise ValueError('certificate must be a JSON object')
    if cert.get('schema') != SCHEMA:
        raise ValueError(f'unsupported or missing schema; expected {SCHEMA}')
    counts = tuple(cert.get(k) for k in ('l', 'm', 'n'))
    if any(type(value) is not int for value in counts):
        raise ValueError('polygon and piece counts must be integers, not booleans')
    l, m, n = counts
    if not (3 <= l <= 100 and 3 <= m <= 100 and 1 <= n <= 1000):
        raise ValueError('invalid counts')
    if expected is not None:
        if (type(expected) not in (tuple, list) or len(expected) != 3
                or any(type(value) is not int for value in expected)):
            raise ValueError('expected target must contain three strict integers')
        if tuple(expected) != counts:
            raise ValueError('certificate is for the wrong target problem')
    _decimal_scalar(cert.get('R'), 'R')
    poses = cert.get('poses')
    if type(poses) is not list or len(poses) != n:
        raise ValueError('poses must be an array with the stated piece count')
    for i, pose in enumerate(poses):
        if type(pose) is not list or len(pose) != 3:
            raise ValueError(f'pose {i} must be an array of length 3')
        for j, value in enumerate(pose):
            _decimal_scalar(value, f'pose {i} scalar {j}')
    witnesses = cert.get('separators')
    if type(witnesses) is not list or len(witnesses) != n * (n - 1) // 2:
        raise ValueError('separators must contain exactly one witness per pair')
    seen = set()
    for witness in witnesses:
        if type(witness) is not dict:
            raise ValueError('separator must be a JSON object')
        i, j = witness.get('i'), witness.get('j')
        if type(i) is not int or type(j) is not int:
            raise ValueError('separator indices must be integers, not booleans')
        if not (0 <= i < j < n) or (i, j) in seen:
            raise ValueError('bad/duplicate pair witness')
        seen.add((i, j))
        axis = witness.get('axis')
        if type(axis) is not list or len(axis) != 2:
            raise ValueError('separator axis must be an array of length 2')
        for k, value in enumerate(axis):
            _decimal_scalar(value, f'separator {(i, j)} axis {k}')


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON object key: {key}')
        result[key] = value
    return result


def _reject_nonfinite(token):
    raise ValueError(f'nonfinite JSON constant forbidden: {token}')


def load_certificate(path):
    # Fractional JSON tokens remain exact during parsing, then geometry schema
    # validation rejects them because geometric values must be quoted strings.
    return json.loads(Path(path).read_text(), parse_float=Decimal,
                      parse_constant=_reject_nonfinite,
                      object_pairs_hook=_unique_object)

def ceildiv(a: int,b: int) -> int:
    if b <= 0: raise ValueError('positive denominator required')
    return -((-a)//b)

@dataclass(frozen=True)
class I:
    lo: int
    hi: int
    def __post_init__(self):
        if self.lo > self.hi: raise ValueError('empty interval')
    @classmethod
    def point(cls, x):
        if isinstance(x,I): return x
        f=Fraction(x); return cls(f.numerator*D//f.denominator,ceildiv(f.numerator*D,f.denominator))
    def __add__(self,b):
        b=I.point(b); return I(self.lo+b.lo,self.hi+b.hi)
    __radd__=__add__
    def __neg__(self): return I(-self.hi,-self.lo)
    def __sub__(self,b): return self+-I.point(b)
    def __rsub__(self,b): return I.point(b)+-self
    def __mul__(self,b):
        b=I.point(b); z=[self.lo*b.lo,self.lo*b.hi,self.hi*b.lo,self.hi*b.hi]
        return I(min(z)//D,ceildiv(max(z),D))
    __rmul__=__mul__
    def __truediv__(self,b):
        b=I.point(b)
        if b.lo <= 0 <= b.hi: raise ZeroDivisionError('interval contains zero')
        f=[Fraction(x*D,y) for x in (self.lo,self.hi) for y in (b.lo,b.hi)]
        low=min(f);high=max(f)
        return I(low.numerator//low.denominator,ceildiv(high.numerator,high.denominator))

def atan_bounds_recip(q: int,terms: int=100):
    # Alternating, decreasing series for atan(1/q), q>1.
    if q<=1 or terms%2: raise ValueError('q>1 and even terms required')
    s=sum((Fraction((-1)**k,(2*k+1)*q**(2*k+1)) for k in range(terms)),Fraction(0))
    r=Fraction(1,(2*terms+1)*q**(2*terms+1))
    return s,s+r # even partial sum lies below atan

def pi_interval():
    a,b=atan_bounds_recip(5);c,d=atan_bounds_recip(239)
    low=16*a-4*d;high=16*b-4*c
    return I(I.point(low).lo,I.point(high).hi)

PI=pi_interval()

def sincos(x: I):
    # Degree-100 Taylor polynomials about 0. All angles must lie in [-8,8].
    if max(abs(x.lo),abs(x.hi))>8*D: raise ValueError('angle outside certified Taylor range [-8,8]')
    term=I.point(1);s=I.point(0);c=I.point(1)
    for k in range(1,101):
        term=term*x/k
        if k%2: s=s+term*((-1)**((k-1)//2))
        else: c=c+term*((-1)**(k//2))
    # For both degree-100 Taylor polynomials, |error| <= 8^101 / 101!.
    e=I.point(Fraction(8**101,factorial(101))).hi
    return I(s.lo-e,s.hi+e),I(c.lo-e,c.hi+e)

def dot(a,b): return a[0]*b[0]+a[1]*b[1]

def dec_grid(x):
    if type(x) is not int:
        raise TypeError('grid endpoint must be an integer')
    whole, remainder = divmod(abs(x), D)
    fractional = f'{remainder:060d}'.rstrip('0')
    sign = '-' if x < 0 else ''
    return sign + str(whole) + ('.' + fractional if fractional else '')

def check(cert, expected=None):
    validate_certificate(cert, expected=expected)
    l,m,n=cert['l'],cert['m'],cert['n']
    if expected is not None and tuple(expected)!=(l,m,n):raise ValueError('certificate is for the wrong target problem')
    if not (isinstance(l,int) and isinstance(m,int) and isinstance(n,int) and 3<=l<=100 and 3<=m<=100 and 1<=n<=1000):
        raise ValueError('invalid counts')
    if len(cert['poses'])!=n: raise ValueError('wrong pose count')
    R=I.point(cert['R'])
    if R.lo<=0: raise ValueError('nonpositive radius')
    v=[]
    for pose in cert['poses']:
        if len(pose)!=3: raise ValueError('pose must have length 3')
        x,y,t=map(I.point,pose);p=[]
        for j in range(m):
            off=PI*Fraction(2*j+(m-1)%2,m)
            si,co=sincos(t+off);p.append((x+si,y+co))
        v.append(p)
    rho=sincos(PI/l)[1];minwall=None
    for k in range(l):
        normal=sincos(PI*Fraction(2*k,l))
        for p in v:
            for vertex in p:
                z=R*rho+dot(normal,vertex)
                if z.lo<0: raise ValueError(f'containment not proved at wall {k}: lower={dec_grid(z.lo)}')
                minwall=z.lo if minwall is None else min(minwall,z.lo)
    expected={(i,j) for i in range(n) for j in range(i+1,n)};seen=set();mingap=None
    for w in cert['separators']:
        i,j=w['i'],w['j']; pair=(i,j)
        if pair not in expected or pair in seen: raise ValueError('bad/duplicate pair witness')
        seen.add(pair)
        if len(w['axis'])!=2: raise ValueError('axis length')
        if all(Fraction(a)==0 for a in w['axis']): raise ValueError('zero axis forbidden')
        a=tuple(map(I.point,w['axis']))
        for u in v[i]:
            for vv in v[j]:
                z=dot(a,(vv[0]-u[0],vv[1]-u[1]))
                if z.lo<0: raise ValueError(f'separation not proved for {pair}: lower={dec_grid(z.lo)}')
                mingap=z.lo if mingap is None else min(mingap,z.lo)
    if seen!=expected: raise ValueError('missing pair witness')
    side=R*sincos(PI/l)[0]/sincos(PI/m)[0]
    return dict(problem=dict(container_sides=l,piece_sides=m,piece_count=n,inner_circumradius=1),status='PASS: all inequalities enclosed with nonnegative rational lower bounds',
        min_containment_lower_bound=dec_grid(minwall),
        min_separation_witness_lower_bound=dec_grid(mingap) if mingap is not None else None,
        unit_side_container_side_interval=[dec_grid(side.lo),dec_grid(side.hi)],
        pair_count=len(seen),vertex_wall_checks=l*m*n,
        vertex_pair_projection_checks=len(seen)*m*m,grid_denominator=str(D))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('certificate',type=Path);parser.add_argument('--expect',type=int,nargs=3,metavar=('L','M','N'));args=parser.parse_args()
    result=check(load_certificate(args.certificate),expected=args.expect);print(json.dumps(result,indent=2))
