from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np, onnx, onnxruntime as ort
from onnx import helper as oh, TensorProto, numpy_helper as nph
from pathlib import Path

app = FastAPI()

def build_rb_sor_model(omega: float = 1.9):
    Uv = oh.make_tensor_value_info("U", TensorProto.FLOAT, ["b","c","h","w"])
    Fv = oh.make_tensor_value_info("F", TensorProto.FLOAT, ["b","c","h","w"])
    Rv = oh.make_tensor_value_info("R", TensorProto.FLOAT, ["b","c","h","w"])
    Bv = oh.make_tensor_value_info("B", TensorProto.FLOAT, ["b","c","h","w"])
    Ov = oh.make_tensor_value_info("Out", TensorProto.FLOAT, ["b","c","h","w"])
    W = nph.from_array(np.array([[[[0,1,0],[1,0,1],[0,1,0]]]], dtype=np.float32), name="W")
    c025 = oh.make_tensor("c025", TensorProto.FLOAT, [], [0.25])
    comega = oh.make_tensor("comega", TensorProto.FLOAT, [], [float(omega)])
    nodes = []
    nodes.append(oh.make_node("Conv", ["U","W"], ["S1"], pads=[1,1,1,1]))
    nodes.append(oh.make_node("Sub", ["S1","F"], ["D1"]))
    nodes.append(oh.make_node("Constant", [], ["C025"], value=c025))
    nodes.append(oh.make_node("Mul", ["D1","C025"], ["J1"]))
    nodes.append(oh.make_node("Sub", ["J1","U"], ["E1"]))
    nodes.append(oh.make_node("Constant", [], ["COM"], value=comega))
    nodes.append(oh.make_node("Mul", ["E1","COM"], ["W1"]))
    nodes.append(oh.make_node("Mul", ["W1","R"], ["WR"]))
    nodes.append(oh.make_node("Add", ["U","WR"], ["Ur"]))
    nodes.append(oh.make_node("Conv", ["Ur","W"], ["S2"], pads=[1,1,1,1]))
    nodes.append(oh.make_node("Sub", ["S2","F"], ["D2"]))
    nodes.append(oh.make_node("Mul", ["D2","C025"], ["J2"]))
    nodes.append(oh.make_node("Sub", ["J2","Ur"], ["E2"]))
    nodes.append(oh.make_node("Mul", ["E2","COM"], ["W2"]))
    nodes.append(oh.make_node("Mul", ["W2","B"], ["WB"]))
    nodes.append(oh.make_node("Add", ["Ur","WB"], ["Out"]))
    g = oh.make_graph(nodes, "rb_sor", [Uv,Fv,Rv,Bv], [Ov], initializer=[W])
    m = oh.make_model(g, opset_imports=[oh.make_operatorsetid("",13)])
    onnx.checker.check_model(m)
    m.ir_version = 11
    return m

def rb_sor_np(U, F, R, B, steps: int, omega: float):
    U = U.copy()
    for _ in range(steps):
        S = np.zeros_like(U, dtype=np.float32)
        S[1:-1,1:-1] = U[:-2,1:-1] + U[2:,1:-1] + U[1:-1,:-2] + U[1:-1,2:]
        J = 0.25*(S - F)
        U = U + R*omega*(J - U)
        S = np.zeros_like(U, dtype=np.float32)
        S[1:-1,1:-1] = U[:-2,1:-1] + U[2:,1:-1] + U[1:-1,:-2] + U[1:-1,2:]
        J = 0.25*(S - F)
        U = U + B*omega*(J - U)
    return U

ART = (Path(__file__).resolve().parents[2] / "artifacts")
ART.mkdir(parents=True, exist_ok=True)

class SolveIn(BaseModel):
    N: int = 64
    steps: int = 400
    omega: float = 1.9

class SolveOut(BaseModel):
    onnx_parity: float
    rel_to_truth: float
    u_mean: float
    u_std: float
    iters: int
    model_path: str

class XiIn(BaseModel):
    N: int = 96
    T: int = 120
    lam: float = 0.2
    m2: float = 0.0
    dt: float = 0.1
    seed: int = 42

class XiOut(BaseModel):
    xi_final: float
    xi_mean: float
    steps: int

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/solve", response_model=SolveOut)
def solve(x: SolveIn):
    N = x.N
    s = x.steps
    om = x.omega
    t = np.linspace(0.0, 1.0, N, dtype=np.float32)
    X, Y = np.meshgrid(t, t, indexing="ij")
    u_true = np.sin(np.pi*X)*np.sin(np.pi*Y)
    sumN_true = np.zeros_like(u_true, dtype=np.float32)
    sumN_true[1:-1,1:-1] = u_true[:-2,1:-1] + u_true[2:,1:-1] + u_true[1:-1,:-2] + u_true[1:-1,2:]
    F = (sumN_true - 4.0*u_true).astype(np.float32)
    R = np.zeros_like(u_true, dtype=np.float32)
    B = np.zeros_like(u_true, dtype=np.float32)
    for i in range(1, N-1):
        for j in range(1, N-1):
            if (i + j) % 2 == 0:
                R[i,j] = 1.0
            else:
                B[i,j] = 1.0
    U0 = np.zeros_like(u_true, dtype=np.float32)
    U_np = rb_sor_np(U0, F, R, B, s, om)
    model = build_rb_sor_model(om)
    p = ART / "poisson_jacobi.onnx"
    with open(str(p), "wb") as f:
        f.write(model.SerializeToString())
    sess = ort.InferenceSession(model.SerializeToString(), providers=["CPUExecutionProvider"])
    U = U0[None,None]
    F4 = F[None,None]
    R4 = R[None,None]
    B4 = B[None,None]
    for _ in range(s):
        U = sess.run(None, {"U":U,"F":F4,"R":R4,"B":B4})[0]
    U_ort = U[0,0]
    rel_parity = float(np.linalg.norm((U_np - U_ort).ravel())/(np.linalg.norm(U_np.ravel()) + 1e-12))
    rel_true = float(np.linalg.norm((U_np - u_true).ravel())/(np.linalg.norm(u_true.ravel()) + 1e-12))
    return {"onnx_parity": rel_parity, "rel_to_truth": rel_true, "u_mean": float(U_np.mean()), "u_std": float(U_np.std()), "iters": s, "model_path": str(p)}

@app.post("/v1/xi/step", response_model=XiOut)
def xi_step(x: XiIn):
    np.random.seed(x.seed)
    phi = np.random.randn(x.N, x.N).astype(np.float32)*0.05
    xis = []
    for _ in range(x.T):
        lap = np.roll(phi,1,0)+np.roll(phi,-1,0)+np.roll(phi,1,1)+np.roll(phi,-1,1)-4*phi
        phi = phi + x.dt*(lap - x.m2*phi - x.lam*phi**3)
        g = np.exp(1j*np.angle(phi + 1e-9))
        xi = np.abs(g.mean())
        xis.append(float(xi))
    return {"xi_final": float(xis[-1]), "xi_mean": float(np.mean(xis)), "steps": x.T}
