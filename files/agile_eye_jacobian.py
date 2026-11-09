"""Agile Eye (3-RRR spherical parallel mechanism, 90-degree links): inverse kinematics, the
Jacobian J = A^-1 B, a finite-difference check, and how isotropy falls off away from home.

Usage: python3 agile_eye_jacobian.py isotropy.png   (needs numpy and matplotlib)
"""
import numpy as np, sys
e = np.eye(3)
u = [e[0], e[1], e[2]]           # base (motor) axes
w0 = [e[1], e[2], e[0]]          # intermediate axes at home
v0 = [e[2], e[0], e[1]]          # platform axes at home

def rot(axis, ang):
    a = axis / np.linalg.norm(axis); K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K

def ik(R, prev=None):
    th = []
    for i in range(3):
        v = R @ v0[i]; a = w0[i] @ v; b = np.cross(u[i], w0[i]) @ v
        t = np.arctan2(-a, b)    # cos t * a + sin t * b = 0, branch nearest home
        cands = [t, t + np.pi, t - np.pi]
        ref = 0.0 if prev is None else prev[i]
        th.append(min(cands, key=lambda c: abs(np.angle(np.exp(1j * (c - ref))))))
    return np.array(th)

def jac(R, th):
    A = np.zeros((3, 3)); B = np.zeros(3)
    for i in range(3):
        w = rot(u[i], th[i]) @ w0[i]; v = R @ v0[i]
        assert abs(w @ v) < 1e-9 and abs(u[i] @ w) < 1e-9
        A[i] = np.cross(w, v); B[i] = np.cross(u[i], w) @ v
    return np.linalg.solve(A, np.diag(B)), A, B    # omega = J thetadot

J, A, B = jac(np.eye(3), ik(np.eye(3)))
print('home J =\n', np.round(J, 6))
# finite-difference check of J at a random pose
rng = np.random.default_rng(1)
R = rot(rng.normal(size=3), 0.4); th = ik(R); J, A, B = jac(R, th)
dth = 1e-6 * rng.normal(size=3)
# move platform by J dth and confirm IK gives th + dth
om = J @ dth; R2 = rot(om, np.linalg.norm(om)) @ R
print('fd error', np.abs(ik(R2, th) - th - dth).max(), 'vs step', np.abs(dth).max())
# condition number vs tilt of the symmetric axis n = (1,1,1)/sqrt3
n = np.ones(3) / np.sqrt(3)
perp = np.cross(n, e[0]); perp /= np.linalg.norm(perp)
for tilt in [0, 10, 20, 30, 40, 50, 60]:
    ks = []
    for az in np.linspace(0, 2 * np.pi, 72, endpoint=False):
        ax = rot(n, az) @ perp
        R = rot(ax, np.radians(tilt)); J = jac(R, ik(R))[0]
        s = np.linalg.svd(J, compute_uv=False); ks.append(s[-1] / s[0])
    print(f'tilt {tilt:2d} deg: 1/cond min {min(ks):.3f} max {max(ks):.3f}')
for tors in [0, 15, 30, 45]:
    R = rot(n, np.radians(tors)); J = jac(R, ik(R))[0]; s = np.linalg.svd(J, compute_uv=False)
    print(f'torsion {tors} deg about n: 1/cond {s[-1]/s[0]:.3f}')

# ---- figure ----
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
tilts = np.linspace(0, 60, 61); lo, hi = [], []
for tilt in tilts:
    ks = []
    for az in np.linspace(0, 2 * np.pi, 72, endpoint=False):
        R = rot(rot(n, az) @ perp, np.radians(tilt)); s = np.linalg.svd(jac(R, ik(R))[0], compute_uv=False); ks.append(s[-1] / s[0])
    lo.append(min(ks)); hi.append(max(ks))
tors = np.linspace(0, 60, 61); kt = []
for t in tors:
    R = rot(n, np.radians(t)); s = np.linalg.svd(jac(R, ik(R))[0], compute_uv=False); kt.append(s[-1] / s[0])
plt.rcParams.update({'font.family': 'serif', 'font.size': 10})
fig, ax = plt.subplots(figsize=(6.4, 3.4), dpi=200)
ax.fill_between(tilts, lo, hi, color='#1a4f9c', alpha=0.25, lw=0)
ax.plot(tilts, lo, color='#1a4f9c', lw=1.4, label='tilt of the platform axis (worst to best direction)')
ax.plot(tors, kt, color='#222', lw=1.4, ls='--', label='twist about the platform axis')
ax.set_xlabel('rotation away from the home pose (degrees)'); ax.set_ylabel('1 / condition number of J')
ax.set_xlim(0, 60); ax.set_ylim(0, 1.05); ax.grid(color='#ddd', lw=0.6); ax.legend(frameon=False, fontsize=9, loc='upper right')
for s_ in ('top', 'right'): ax.spines[s_].set_visible(False)
fig.tight_layout(); fig.savefig(sys.argv[1], facecolor='white'); print('saved')
