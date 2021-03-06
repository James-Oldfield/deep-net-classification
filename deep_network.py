import numpy as np

from activations import relu, d_relu, sigmoid, d_sigmoid
from sklearn.utils import shuffle


class DeepNet(object):
    def __init__(self, architecture):
        """Initalise the weights, biases, etc.

        :param architecture: A list containing the network's desired
            layer architecture. [2, 5, 5, 1] would contain two 5 unit hidden
            layers, for example.
        :return: The parameters dictionary with initialised weights + biases.
        """

        self.parameters = {}  # stores the weights, biases, etc.
        self.L = len(architecture)  # no. of layers
        a = architecture

        """Initialise all the weights and biases in the network, given
        the architecture requested. Biases are zero initalised. Weights
        are randomly initalised from Gaussian dist.
        """
        for l in range(1, self.L):
            self.parameters['W{}'.format(l)] = np.random.randn(a[l],
                                                               a[l-1]) * 0.01
            self.parameters['b{}'.format(l)] = np.zeros((a[l], 1))

    def get_parameters(self):
        """Return the net's params.

        :return: net's params.
        """

        return self.parameters

    def activate(self, A_prev, W, b, activ_fn=relu):
        """Compute a layer's activation values, given the previous layer's.

        :param A_prev: previous layer's activations.
        :param W: Weights max to compute next layer.
        :param b: ditto above, but for bias term.
        :param activ_fn: desired activation function.
        :return A, (cache): activation for this layer + useful
            values from this layer for backprop.
        """

        Z = np.dot(W, A_prev) + b
        A = activ_fn(Z)

        # store the reference to derivative of correct function
        if activ_fn is relu:
            d_func = d_relu
        else:
            d_func = d_sigmoid

        return A, (A_prev, W, b, Z, d_func)

    def feedforward(self, A):
        """Forward propagate using ReLu activation functions up to
        layer (L-1), and then a sigmoid activation for the output.

        :param A: The training data set (or minibatch subset)
        """

        caches = []
        L = len(self.parameters) // 2

        # Compute each layer's activations using ReLu, up until L-1.
        # Store the relevant values in `cache` list for use with bprop.
        for l in range(1, L):
            A_prev = A
            W = self.parameters['W{}'.format(l)]
            b = self.parameters['b{}'.format(l)]

            A, cache = self.activate(A_prev, W, b)
            caches.append(cache)

        # Compute the output layer's value using sigmoid.
        WL = self.parameters['W{}'.format(L)]
        bL = self.parameters['b{}'.format(L)]
        AL, cache = self.activate(A, WL, bL, activ_fn=sigmoid)

        caches.append(cache)

        return AL, caches

    def backpropagate(self, AL, Y, caches):
        """Backpropagate the error to all the weights, etc.

        :param AL: The activation value of layer `L` (output).
        :param Y: Ground truth Y values.
        :param caches: All the cache values computed in forward prop.
        :return: a dictionary of the gradients of all the parameters
            for the net.
        """

        grads = {}
        L = len(caches)
        Y = Y.reshape(AL.shape)

        # Store the deriv. wrt the output layer
        dAL = - (np.divide(Y, AL) - np.divide(1 - Y, 1 - AL))

        current_cache = caches[-1]

        # store the gradients of the output layer.
        grads['dA{}'.format(L)], grads["dW{}".format(L)], grads["db{}".format(L)] = self.get_prevlayer_gradient(dAL, current_cache, activ_fn=sigmoid)  # noqa: E501

        for l in reversed(range(L-1)):
            current_cache = caches[l]

            dA_prev_temp, dW_temp, db_temp = self.get_prevlayer_gradient(
                grads["dA{}".format(L)], current_cache)

            grads["dA{}".format(l+1)] = dA_prev_temp
            grads["dW{}".format(l+1)] = dW_temp
            grads["db{}".format(l+1)] = db_temp

        return grads

    def SGD(self,
            training_data,
            num_epochs=30,
            mini_batch_size=10,
            eta=0.5,
            test_data=None,
            save_costs=False):

        X, y = training_data
        m = len(X)
        costs = []

        for epoch in range(num_epochs):
            print('Training epoch #{}\n\n'.format(epoch + 1))

            # shuffle the data set
            X, y = shuffle(X, y, random_state=0)

            mini_batches = [
                [X[k:k+mini_batch_size],
                 y[k:k+mini_batch_size]]
                for k in range(0, m, mini_batch_size)]

            for batch_num, mini_batch in enumerate(mini_batches):
                X_mini, y_mini = mini_batch
                y_mini = np.asarray(y_mini).T

                # first, compute the activation in layer L for this mini_batch
                AL, caches = self.feedforward(X_mini.T)
                # then the cost for this mini batch
                cost = self.get_cost(AL, y_mini)
                # then get the gradients w/r/t cost function
                grads = self.backpropagate(AL, y_mini, caches)

                # finally, update the object's params.
                self.update_params(grads, eta)

                if batch_num % 100 == 0:
                    # store the costs to inspect performance
                    costs.append(cost)

                    print('Cost after iteration {}: {} in epoch #{}'.format(
                        batch_num, cost, epoch+1))
            if test_data:
                self.predict(test_data)

        if save_costs:
            import matplotlib.pyplot as pp
            pp.plot(costs, 'x')
            pp.show()

    def update_params(self, grads, eta):
        """Update the object's params using learning rate eta
        (assumes we've already) performed desired step of backprop,
        with an appropriately size minibatch.

        :param grads: the dictionary of gradients to use to update.
        :param eta: learning rate for GD.
        """

        L = len(self.parameters) // 2  # cache no. of layers
        for l in range(L):
            self.parameters['W{}'.format(l+1)] = \
                self.parameters['W{}'.format(l+1)] \
                - eta * grads['dW{}'.format(l+1)]
            self.parameters['b{}'.format(l+1)] = \
                self.parameters['b{}'.format(l+1)] \
                - eta * grads['db{}'.format(l+1)]

    def get_prevlayer_gradient(self, dA, cache, activ_fn=relu):
        """Compute the gradient of layer (l-1) w/r/t cost, given
        the derivative of the cost function w/r/t layer `l`.

        :param dA: gradient of cost function w/r/t current layer.
        :param cache: the cache of the layer's values.
        :param activ_fn: the activation function used in this layer.
        :return: The derivative of cost fn, w/r/t desired vals.
        """

        A_prev, W, b, Z, d_func = cache
        dZ = np.multiply(dA, d_func(Z))

        m = A_prev.shape[1]

        dW = (1/m) * np.dot(dZ, A_prev.T)
        db = (1/m) * np.sum(dZ, axis=1, keepdims=True)
        dA_prev = np.dot(W.T, dZ)

        return dA_prev, dW, db

    def get_cost(self, YHat, Y):
        """Compute the Cross Entropy cost, given our prediction and ground truth y.

        :param YHat: our approximation of Y.
        :param Y: the actual value of Y.
        :return: the cost, as specified by the cross entropy function.
        """
        m = len(Y)  # no. of examples

        # Compute the Cross Entropy cost, given the predicted values
        # and the ground truth values
        cost = -(1/m) * np.sum(np.nan_to_num(
            Y * np.log(YHat) + (1-Y) * np.log(1-YHat)))

        return np.squeeze(cost)

    def predict(self, data):
        X, y = data
        X = X.T
        y = np.asarray(y).T

        m = X.shape[1]

        probs, _ = self.feedforward(X)

        print('-----------')
        print('Accuracy against test set: ' + str(np.sum((
            np.argmax(probs.T, axis=1) == np.argmax(y, axis=1)) / m)))
        print('-----------')
