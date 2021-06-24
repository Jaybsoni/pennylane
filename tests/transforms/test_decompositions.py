# Copyright 2018-2021 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Tests for the QubitUnitary decomposition transforms.
"""

import pytest

import pennylane as qml
from pennylane import numpy as np

from pennylane.wires import Wires
from pennylane.transforms import decompose_single_qubit_unitaries
from pennylane.transforms.decompositions import _zyz_decomposition

from gate_data import I, Z, S, T, H, X

single_qubit_decomps = [
    # First set of gates are diagonal and converted to RZ
    (I, qml.RZ, [0.0]),
    (Z, qml.RZ, [np.pi]),
    (S, qml.RZ, [np.pi / 2]),
    (T, qml.RZ, [np.pi / 4]),
    (qml.RZ(0.3, wires=0).matrix, qml.RZ, [0.3]),
    (qml.RZ(-0.5, wires=0).matrix, qml.RZ, [-0.5]),
    # Next set of gates are non-diagonal and decomposed as Rots
    (H, qml.Rot, [np.pi, np.pi / 2, 0.0]),
    (X, qml.Rot, [0.0, np.pi, np.pi]),
    (qml.Rot(0.2, 0.5, -0.3, wires=0).matrix, qml.Rot, [0.2, 0.5, -0.3]),
    (np.exp(1j * 0.02) * qml.Rot(-1.0, 2.0, -3.0, wires=0).matrix, qml.Rot, [-1.0, 2.0, -3.0]),
]

# A simple quantum function for testing
def qfunc(U):
    qml.Hadamard(wires="a")
    qml.QubitUnitary(U, wires="a")
    qml.CNOT(wires=["b", "a"])


class TestQubitUnitaryZYZDecomposition:
    """Test that the decompsoitions are correct."""

    def test_zyz_decomposition_invalid_input(self):
        with pytest.raises(ValueError, match="Operator must be unitary"):
            _zyz_decomposition(I + H, Wires("a"))

    @pytest.mark.parametrize("U,expected_gate,expected_params", single_qubit_decomps)
    def test_zyz_decomposition(self, U, expected_gate, expected_params):
        """Test that a one-qubit matrix in isolation is correctly decomposed."""
        obtained_gates = _zyz_decomposition(U, Wires("a"))

        assert len(obtained_gates) == 1

        assert isinstance(obtained_gates[0], expected_gate)
        assert obtained_gates[0].wires == Wires("a")
        assert qml.math.allclose(obtained_gates[0].parameters, expected_params)

    @pytest.mark.parametrize("U,expected_gate,expected_params", single_qubit_decomps)
    def test_zyz_decomposition_torch(self, U, expected_gate, expected_params):
        """Test that a one-qubit operation in Torch is correctly decomposed."""
        torch = pytest.importorskip("torch")

        U = torch.tensor(U, dtype=torch.complex64)

        obtained_gates = _zyz_decomposition(U, wire="a")

        assert len(obtained_gates) == 1
        assert isinstance(obtained_gates[0], expected_gate)
        assert obtained_gates[0].wires == Wires("a")
        assert qml.math.allclose(
            [x.detach() for x in obtained_gates[0].parameters], expected_params
        )

    @pytest.mark.parametrize("U,expected_gate,expected_params", single_qubit_decomps)
    def test_zyz_decomposition_tf(self, U, expected_gate, expected_params):
        """Test that a one-qubit operation in Tensorflow is correctly decomposed."""
        tf = pytest.importorskip("tensorflow")

        U = tf.Variable(U, dtype=tf.complex64)

        obtained_gates = _zyz_decomposition(U, wire="a")

        assert len(obtained_gates) == 1
        assert isinstance(obtained_gates[0], expected_gate)
        assert obtained_gates[0].wires == Wires("a")
        assert qml.math.allclose([x.numpy() for x in obtained_gates[0].parameters], expected_params)

    @pytest.mark.parametrize("U,expected_gate,expected_params", single_qubit_decomps)
    def test_zyz_decomposition_jax(self, U, expected_gate, expected_params):
        """Test that a one-qubit operation in JAX is correctly decomposed."""
        jax = pytest.importorskip("jax")

        U = jax.numpy.array(U, dtype=jax.numpy.complex64)

        obtained_gates = _zyz_decomposition(U, wire="a")

        assert len(obtained_gates) == 1
        assert isinstance(obtained_gates[0], expected_gate)
        assert obtained_gates[0].wires == Wires("a")
        assert qml.math.allclose(
            [jax.numpy.asarray(x) for x in obtained_gates[0].parameters], expected_params
        )


class TestDecomposeSingleQubitUnitaryTransform:
    """Tests to ensure the transform itself works in all interfaces."""

    @pytest.mark.parametrize("U,expected_gate,expected_params", single_qubit_decomps)
    def test_decompose_single_qubit_unitaries(self, U, expected_gate, expected_params):
        transformed_qfunc = decompose_single_qubit_unitaries(qfunc)

        ops = qml.transforms.make_tape(transformed_qfunc)(U).operations

        assert len(ops) == 3

        assert isinstance(ops[0], qml.Hadamard)
        assert ops[0].wires == Wires("a")

        assert isinstance(ops[1], expected_gate)
        assert ops[1].wires == Wires("a")
        assert qml.math.allclose(ops[1].parameters, expected_params)

        assert isinstance(ops[2], qml.CNOT)
        assert ops[2].wires == Wires(["b", "a"])

    @pytest.mark.parametrize("U,expected_gate,expected_params", single_qubit_decomps)
    def test_decompose_single_qubit_unitaries_torch(self, U, expected_gate, expected_params):
        torch = pytest.importorskip("torch")

        U = torch.tensor(U, dtype=torch.complex64)

        transformed_qfunc = decompose_single_qubit_unitaries(qfunc)

        ops = qml.transforms.make_tape(transformed_qfunc)(U).operations

        assert len(ops) == 3

        assert isinstance(ops[0], qml.Hadamard)
        assert ops[0].wires == Wires("a")

        assert isinstance(ops[1], expected_gate)
        assert ops[1].wires == Wires("a")
        assert qml.math.allclose([x.detach() for x in ops[1].parameters], expected_params)

        assert isinstance(ops[2], qml.CNOT)
        assert ops[2].wires == Wires(["b", "a"])

    @pytest.mark.parametrize("U,expected_gate,expected_params", single_qubit_decomps)
    def test_decompose_single_qubit_unitaries_tf(self, U, expected_gate, expected_params):
        tf = pytest.importorskip("tensorflow")

        U = tf.Variable(U, dtype=tf.complex64)

        transformed_qfunc = decompose_single_qubit_unitaries(qfunc)

        ops = qml.transforms.make_tape(transformed_qfunc)(U).operations

        assert len(ops) == 3

        assert isinstance(ops[0], qml.Hadamard)
        assert ops[0].wires == Wires("a")

        assert isinstance(ops[1], expected_gate)
        assert ops[1].wires == Wires("a")
        assert qml.math.allclose([x.numpy() for x in ops[1].parameters], expected_params)

        assert isinstance(ops[2], qml.CNOT)
        assert ops[2].wires == Wires(["b", "a"])

    @pytest.mark.parametrize("U,expected_gate,expected_params", single_qubit_decomps)
    def test_decompose_single_qubit_unitaries_jax(self, U, expected_gate, expected_params):
        jax = pytest.importorskip("jax")

        U = jax.numpy.array(U, dtype=jax.numpy.complex64)

        transformed_qfunc = decompose_single_qubit_unitaries(qfunc)

        ops = qml.transforms.make_tape(transformed_qfunc)(U).operations

        assert len(ops) == 3

        assert isinstance(ops[0], qml.Hadamard)
        assert ops[0].wires == Wires("a")

        assert isinstance(ops[1], expected_gate)
        assert ops[1].wires == Wires("a")
        assert qml.math.allclose([jax.numpy.asarray(x) for x in ops[1].parameters], expected_params)

        assert isinstance(ops[2], qml.CNOT)
        assert ops[2].wires == Wires(["b", "a"])


# A simple circuit; we will test QubitUnitary on matrices constructed using trainable
# parameters, and RZ/RX are easy to write the matrices for.
def original_qfunc_for_grad(angles):
    qml.Hadamard(wires="a")
    qml.RZ(angles[0], wires="a")
    qml.RX(angles[1], wires="b")
    qml.CNOT(wires=["b", "a"])
    return qml.expval(qml.PauliX(wires="a"))


dev = qml.device("default.qubit", wires=["a", "b"])

angle_pairs = [(0.3, 0.3), (np.pi, -0.65), (0.0, np.pi / 2), (np.pi / 3, 0.0)]


class TestQubitUnitaryDifferentiability:
    """Tests to ensure the transform is fully differentiable in all interfaces."""

    @pytest.mark.parametrize("x_rot,z_rot", angle_pairs)
    def test_gradient_qubit_unitary(self, x_rot, z_rot):
        """Tests differentiability in autograd interface."""

        def qfunc_with_qubit_unitary(angles):
            z = angles[0]
            x = angles[1]
            Z_mat = np.array([[qml.math.exp(-1j * z / 2), 0], [0, qml.math.exp(1j * z / 2)]])
            X_mat = np.array(
                [
                    [qml.math.cos(x / 2), -1j * qml.math.sin(x / 2)],
                    [-1j * qml.math.sin(x / 2), qml.math.cos(x / 2)],
                ]
            )

            qml.Hadamard(wires="a")
            qml.QubitUnitary(Z_mat, wires="a")
            qml.QubitUnitary(X_mat, wires="b")
            qml.CNOT(wires=["b", "a"])
            return qml.expval(qml.PauliX(wires="a"))

        transformed_qfunc = decompose_single_qubit_unitaries(qfunc_with_qubit_unitary)

        original_qnode = qml.QNode(original_qfunc_for_grad, dev)
        transformed_qnode = qml.QNode(transformed_qfunc, dev)

        input = np.array([x_rot, z_rot], requires_grad=True)
        assert qml.math.allclose(original_qnode(input), transformed_qnode(input))

        original_grad = qml.grad(original_qnode)(input)
        transformed_grad = qml.grad(transformed_qnode)(input)
        assert qml.math.allclose(original_grad, transformed_grad)

    @pytest.mark.parametrize("x_rot,z_rot", angle_pairs)
    def test_gradient_qubit_unitary_torch(self, x_rot, z_rot):
        """Tests differentiability in torch interface."""
        torch = pytest.importorskip("torch")

        def qfunc_with_qubit_unitary(angles):
            z = angles[0]
            x = angles[1]
            Z_mat = torch.tensor(
                [[qml.math.exp(-1j * z / 2), 0.0], [0.0, qml.math.exp(1j * z / 2)]]
            )
            X_mat = torch.tensor(
                [
                    [qml.math.cos(x / 2), -1j * qml.math.sin(x / 2)],
                    [-1j * qml.math.sin(x / 2), qml.math.cos(x / 2)],
                ]
            )

            qml.Hadamard(wires="a")
            qml.QubitUnitary(Z_mat, wires="a")
            qml.QubitUnitary(X_mat, wires="b")
            qml.CNOT(wires=["b", "a"])
            return qml.expval(qml.PauliZ(wires="a"))

        transformed_qfunc = decompose_single_qubit_unitaries(qfunc_with_qubit_unitary)

        original_qnode = qml.QNode(original_qfunc_for_grad, dev, interface="torch")
        transformed_qnode = qml.QNode(transformed_qfunc, dev, interface="torch")

        original_input = torch.tensor([x_rot, z_rot], requires_grad=True)
        original_result = original_qnode(original_input)
        transformed_input = torch.tensor([x_rot, z_rot], requires_grad=True)
        transformed_result = transformed_qnode(transformed_input)
        assert qml.math.allclose(original_result, transformed_result)

        original_result.backward()
        transformed_result.backward()

        assert qml.math.allclose(original_result.grad, transformed_result.grad)

    @pytest.mark.parametrize("x_rot,z_rot", angle_pairs)
    def test_decompose_single_qubit_unitaries_tf(self, x_rot, z_rot):
        """Tests differentiability in tensorflow interface."""
        tf = pytest.importorskip("tensorflow")

        def qfunc_with_qubit_unitary(angles):
            z = angles[0]
            x = angles[1]
            Z_mat = tf.Variable([[qml.math.exp(-1j * z / 2), 0.0], [0.0, qml.math.exp(1j * z / 2)]])
            X_mat = tf.Variable(
                [
                    [qml.math.cos(x / 2), -1j * qml.math.sin(x / 2)],
                    [-1j * qml.math.sin(x / 2), qml.math.cos(x / 2)],
                ]
            )

            qml.Hadamard(wires="a")
            qml.QubitUnitary(Z_mat, wires="a")
            qml.QubitUnitary(X_mat, wires="b")
            qml.CNOT(wires=["b", "a"])
            return qml.expval(qml.PauliX(wires="a"))

        transformed_qfunc = decompose_single_qubit_unitaries(qfunc_with_qubit_unitary)

        original_qnode = qml.QNode(original_qfunc_for_grad, dev, interface="tf")
        transformed_qnode = qml.QNode(transformed_qfunc, dev, interface="tf")

        original_input = tf.Variable([x_rot, z_rot])
        original_result = original_qnode(original_input)
        transformed_input = tf.Variable([x_rot, z_rot])
        transformed_result = transformed_qnode(transformed_input)
        assert qml.math.allclose(original_result, transformed_result)

        with tf.GradientTape() as tape:
            loss = original_qnode(original_input)
        original_grad = tape.gradient(loss, original_input)

        with tf.GradientTape() as tape:
            loss = transformed_qnode(transformed_input)
        transformed_grad = tape.gradient(loss, transformed_input)

        assert qml.math.allclose(original_grad, transformed_grad)

    @pytest.mark.parametrize("x_rot,z_rot", angle_pairs)
    def test_decompose_single_qubit_unitaries_jax(self, x_rot, z_rot):
        """Tests differentiability in jax interface."""
        jax = pytest.importorskip("jax")
        from jax import numpy as jnp

        def qfunc_with_qubit_unitary(angles):
            z = angles[0]
            x = angles[1]
            Z_mat = jnp.array(
                [[qml.math.exp(-1j * z / 2), 0.0], [0.0, qml.math.exp(1j * z / 2)]],
            )
            X_mat = jnp.array(
                [
                    [qml.math.cos(x / 2), -1j * qml.math.sin(x / 2)],
                    [-1j * qml.math.sin(x / 2), qml.math.cos(x / 2)],
                ],
            )

            qml.Hadamard(wires="a")
            qml.QubitUnitary(Z_mat, wires="a")
            qml.QubitUnitary(X_mat, wires="b")
            qml.CNOT(wires=["b", "a"])
            return qml.expval(qml.PauliX(wires="a"))

        transformed_qfunc = decompose_single_qubit_unitaries(qfunc_with_qubit_unitary)

        original_qnode = qml.QNode(original_qfunc_for_grad, dev, interface="jax")
        transformed_qnode = qml.QNode(transformed_qfunc, dev, interface="jax")

        original_input = jnp.array([x_rot, z_rot], dtype=jnp.complex64)
        original_result = original_qnode(original_input)
        transformed_input = jnp.array([x_rot, z_rot], dtype=jnp.complex64)
        transformed_result = transformed_qnode(transformed_input)
        assert qml.math.allclose(original_result, transformed_result)

        original_grad = jax.grad(original_qnode)(original_input)
        transformed_grad = jax.grad(transformed_qnode)(transformed_input)
        assert qml.math.allclose(original_grad, transformed_grad)
