from abc import ABC, abstractmethod
from enum import Enum
import numpy as np
import networkx as nx
import math
from NN.NN_graph import plot_neural_network
import matplotlib.pyplot as plt
import pandas as pd
from ucimlrepo import fetch_ucirepo
import pickle

class Function(ABC):
    
    @abstractmethod
    def activation(self):
        pass
    
    @abstractmethod
    def derivate(self):
        pass

class Id(Function):

    def activation(self):
        def id(x):
            return x
        return id

    def derivate(self):
        def id_der(x):
            return 1
        return id_der

class Relu(Function):

    def activation(self):
        def relu(x):
            return np.max(x,0)
        return relu

    def derivate(self):
        def relu_der(x):
            if (x < 0): return 0
            return 1
        return relu_der

class Sigmoid(Function):

    def __init__(self, a):
        self.a = a

    def activation(self):
        def sigmoid(x):
            return 1 / (1 + np.exp(-(self.a * x)))
        return sigmoid

    def derivate(self):
        def sigmoid_der(x):
            return self.activation()(x)*(1-self.activation()(x))
        return sigmoid_der

class Tanh(Function):

    def __init__(self, a):
        self.a = a

    def activation(self):
        def tanh(x):
            return np.tanh(self.a*x/2)
        return tanh
    
    def derivate(self):
        def tanh_der(x):
            return 1 - (self.activation()(x))**2
        return tanh_der

class Type(Enum):
    INPUT = 1
    HIDDEN = 2
    OUTPUT = 3

class Layer:

    def __init__(self, neurons, weights, activation_class, layer_type, weight_scaling = 1):
        self.neurons = neurons
        self.type = layer_type
        self.activation_function = activation_class.activation()
        self.activation_derivate = activation_class.derivate()
        if layer_type == Type.INPUT:
            self.weights = weights
            self.weight_matrix = np.eye(neurons)
        else:
            self.weights = weights + 1
            self.weight_matrix = (np.random.uniform(-weight_scaling, weight_scaling, (self.neurons, self.weights)))

    def net(self, o):
        if self.type != Type.INPUT:
            o = np.concatenate((np.array([1]), o))
        return np.dot(self.weight_matrix, o)

    def act(self, o):
        f = np.vectorize(self.activation_function)
        return f(self.net(o))

    def der_act(self, o):
        f = np.vectorize(self.activation_derivate)
        return f(self.net(o))

class Network:

    def __init__(self, weigth_scaling, hidden_layers_number, input_dimension, layer_length, activation_class_arr, TR_std_mean_arr):
        self.depth = hidden_layers_number
        self.std_mean_arr = TR_std_mean_arr
        self.store_hidden_result = [] 
        self.input_layer = Layer(input_dimension, input_dimension, Id(), Type.INPUT)
        self.hidden_layers = np.empty(self.depth, dtype=object)
        self.hidden_layers[0] = Layer(layer_length[0], input_dimension, activation_class_arr[0], Type.HIDDEN, weigth_scaling)
        self.store_hidden_result.append(np.zeros(self.hidden_layers[0].neurons))
        for i in range(hidden_layers_number - 1):
            self.hidden_layers[i + 1] = Layer(layer_length[i + 1], self.hidden_layers[i].neurons, activation_class_arr[i + 1], Type.HIDDEN, weigth_scaling)
            self.store_hidden_result.append(np.zeros(self.hidden_layers[i + 1].neurons))
        self.output_layer = Layer(layer_length[hidden_layers_number], self.hidden_layers[hidden_layers_number - 1].neurons, activation_class_arr[hidden_layers_number], Type.OUTPUT, weigth_scaling)

    def reset(self, weight_scaling = 0.5):
        for i in range(self.depth):
            current_hidden_layer = self.hidden_layers[i]
            current_hidden_layer.weight_matrix = (np.random.uniform(-weight_scaling, weight_scaling, (current_hidden_layer.neurons, current_hidden_layer.weights)))
        self.output_layer.weight_matrix = (np.random.uniform(-weight_scaling, weight_scaling, (self.output_layer.neurons, self.output_layer.weights)))

    def plot_error(self, errors, validation_errors, filename):
        plot = plt.figure(figsize=(16, 9))
        plt.plot(range(len(errors)), errors, c = "blue", label = 'Training error')
        plt.plot(range(len(validation_errors)), validation_errors, c = "red", label = "Validation error")
        plt.title("Curva dell'Errore LED all'aumentare delle epoche")
        plt.xlabel("Epoche")
        plt.ylabel("Errore")
        plt.legend()
        plt.savefig("Plot/Png/" + filename + ".png")
        with open("Plot/Pickle/" + filename + ".pkl", "wb") as f:
            pickle.dump(plot, f)
        plt.show()
        plt.close()
        
    def plot_output(self, X, y, title = " "):
        data = []
        for i in range(len(X)):
            output = (self.network_output(X.iloc[i])*self.std_mean_arr["y_train_std"]) + self.std_mean_arr["y_train_mean"]
            data.append({
                'target_x': output.iloc[0],
                'target_y': output.iloc[1],
                'target_z': output.iloc[2],
            })
        data = pd.DataFrame(data)
        fig = plt.figure(figsize=(9, 9))
        ax = fig.add_subplot(111, projection='3d')  # Grafico 3D

        # Plot dei punti
        ax.scatter(y['target_x'], y['target_y'], y['target_z'], c='blue', marker='o', label="Target value", s=50)  # Scatter plot
        ax.scatter(data['target_x'], data['target_y'], data['target_z'], c='red', marker='o', label="Network output", s=50)  # Scatter plot

        plt.legend()

        # Personalizzazione
        ax.set_title(title)
        ax.set_xlabel('Asse X')
        ax.set_ylabel('Asse Y')
        ax.set_zlabel('Asse Z')

        x_min = min(y['target_x'].min(), data['target_x'].min())
        x_max = max(y['target_x'].max(), data['target_x'].max())
        y_min = min(y['target_y'].min(), data['target_y'].min())
        y_max = max(y['target_y'].max(), data['target_y'].max())
        z_min = min(y['target_z'].min(), data['target_z'].min())
        z_max = max(y['target_z'].max(), data['target_z'].max())

        ax.set_xlim([x_min, x_max])
        ax.set_ylim([y_min, y_max])
        ax.set_zlim([z_min, z_max])
        # Mostra il grafico
        plt.tight_layout()
        plt.show()

    def plot(self):

        def weight_to_color (x):
            return [0, 0, 1] if x < 0 else [1, 0, 0]

        #scelgo la trasparenza in base al valore assoluto del rapporto tra il peso considerato e il valore assoluto del peso massimo
        def weight_alpha(x): 
            alpha = np.abs(np.divide(x,1))
            return alpha

        G = nx.DiGraph()
        layers = []
        layers.append(self.input_layer.neurons)
        for i in range(self.depth):
            layers.append(self.hidden_layers[i].neurons)
        layers.append(self.output_layer.neurons)

        pos = {}
        node_labels = {}
        node_colors = {}
        node_sizes = {}
        y_offset = 0
        max_layers = np.max(layers[1:])
        
        for layer, n_units in enumerate(layers):
            if layer != len(layers) - 1:
                y_offset = -(n_units/2)
                node_id_minus_one = f"L{layer}_N{-1}"
                G.add_node(node_id_minus_one)  
                node_sizes [node_id_minus_one] = 200
                node_labels[node_id_minus_one] = " "
                node_colors[node_id_minus_one] = "yellow"
                pos[node_id_minus_one] = (layer / 2, - (max_layers/2+1))
        
            for unit in range(n_units):
                node_id = f"L{layer}_N{unit}"
                G.add_node(node_id)
                if layer == 0:
                    y_offset = -((n_units-1))/2
                    pos[node_id] = (layer / 2, y_offset + unit)
                    node_sizes [node_id] = 200
                    node_labels[node_id] = " "  
                    node_colors[node_id] = "gray"
                elif layer < len(layers)-1: 
                    y_offset = -((n_units-1))/2
                    pos[node_id] = (layer / 2, y_offset + unit)
                    node_sizes [node_id] = 200
                    node_labels[node_id] = " "  
                    node_colors[node_id] = "green"
                else:
                    y_offset = -((n_units-1))/2
                    pos[node_id] = (layer / 2, y_offset + unit)
                    node_sizes [node_id] = 200
                    node_labels[node_id] = " "
                    node_colors[node_id] = "green"

        #mette gli edge tra i neuroni
        for layer in range(self.depth+1):
            for src in range(-1, layers[layer]):
                for dest in range(layers[layer + 1]):
                    src_id = f"L{layer}_N{src}"
                    dest_id = f"L{layer + 1}_N{dest}"
                    if (layer < self.depth):
                        G.add_edge(src_id, dest_id)
                        G[src_id][dest_id]["weight"] = self.hidden_layers[layer].weight_matrix[dest][src]
                    elif (layer == ((self.depth))):
                        G.add_edge(src_id, dest_id)
                        G[src_id][dest_id]["weight"] = self.output_layer.weight_matrix[dest][src]
                        

        edge_colors = []
        for u, v in G.edges():
            weight = G[u][v]["weight"] 
            color = weight_to_color(weight)
            alpha = weight_alpha(weight)
            edge_colors.append((color[0], color[1], color[2], alpha)) 
        
        #disegna la figura
        node_colors_list = np.array(list(node_colors.values()))
        node_sizes_list = np.array(list(node_sizes.values()))
        plt.figure(figsize=(16, 10))
        nx.draw_networkx_nodes(G, pos, node_color=node_colors_list, node_size=node_sizes_list, edgecolors="black")
        nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=12, font_color="black")
        nx.draw_networkx_edges(G, pos, edge_color=edge_colors, width=3, arrows=False)

        plt.axis('off')

        # Adatta l'aspetto della figura all'interno della finestra
        plt.tight_layout()

        plt.show()

    def network_output(self, input):
        current_input = self.input_layer.act(input)
        self.store_hidden_result[0] = self.hidden_layers[0].act(current_input)
        for i in range(self.depth-1):
            self.store_hidden_result[i + 1] = self.hidden_layers[i + 1].act(self.store_hidden_result[i])
        return self.output_layer.act(self.store_hidden_result[self.depth - 1])

    #nota: LMS e backprop. tengono conto di target value monodimensionali, quindi supponiamo di avere un solo neurone di output
    def LMS_classification(self, X, y, threshold=0.5, positive=1, negative=0, mean = False):
        error = 0
        X_stand = self.standard(X)
        for i in range(len(X)):
            output = self.unstandard(self.network_output(X_stand.iloc[i],y))
            if output >= threshold:
                discrete_output = positive
            else:
                discrete_output = negative
            target_value = y.iloc[i]
            error += (target_value - discrete_output)**2
        if mean: 
            return (error / len(X))
        return error
    
    def LMS_regression(self,X,y, mean = False):
        error=0
        for i in range(len(X)):
            output = self.network_output(X.iloc[i])
            error += np.dot(y.iloc[i] - output, y.iloc[i] - output)
        if mean:
            return (error / len(X))
        return error
    
    def LED_regression(self, X, y, mean = False):
        error = 0
        for i in range(len(X)):
            output = (self.network_output(X.iloc[i])*self.std_mean_arr["y_train_std"]) + self.std_mean_arr["y_train_mean"]
            error += np.sqrt(np.dot((y.iloc[i] - output), (y.iloc[i] - output)))
        if mean:
            return (error / len(X))
        return error
    
    def backpropagation_batch(self, X, y, regression = True, batches_number = 100, eta = 0.1, lambda_tichonov=0, alpha=0, validation = None, plot=False):
        X_stand = (X - self.std_mean_arr["X_train_mean"]) / self.std_mean_arr["X_train_std"]
        y_stand = (y - self.std_mean_arr["y_train_mean"]) / self.std_mean_arr["y_train_std"]
        if validation:
            validation_input_stand = (validation[0]-self.std_mean_arr["X_train_mean"])/self.std_mean_arr["X_train_std"]
        errors = []
        validation_errors = []
        #inizializzo la matrice che conterrà la somma di tutte le matrici store_gradient per ogni hidden layer
        batch_gradient = [[np.zeros((self.hidden_layers[i].neurons, self.hidden_layers[i].weights)) for i in range(self.depth)]for i in range(2)]
        #aggiungo l'ultimo pezzo di batch_gradient che conterrà la somma di tutti i gradienti per l'output layer
        batch_gradient[0].append(np.zeros((self.output_layer.neurons, self.output_layer.weights)))
        batch_gradient[1].append(np.zeros((self.output_layer.neurons, self.output_layer.weights)))
        for i in range(batches_number):
            print(f"Iterazione {i}")
            if regression:
                errors.append(self.LED_regression(X_stand, y, mean = True))
            else: 
                errors.append(self.LMS_classification(X, y))
            if validation: 
                if regression:
                    validation_errors.append(self.LED_regression(validation_input_stand, validation[1], mean = True))
                else: 
                    validation_errors.append(self.LMS_classification(validation[0], validation[1]))
            #itero sul dataset
            for j in range(self.depth):
                batch_gradient[1][j] = lambda_tichonov * self.hidden_layers[j].weight_matrix
                self.hidden_layers[j].weight_matrix += (alpha / len(X) * batch_gradient[0][j])
            self.output_layer.weight_matrix += (alpha / len(X) * batch_gradient[0][-1])
            batch_gradient[0] = self.backpropagation_iteration(X_stand.iloc[0], y_stand.iloc[0])
            for i in range(1, len(X)):
                current_gradient = self.backpropagation_iteration(X_stand.iloc[i], y_stand.iloc[i]) #Nell'allenamento utilizza i target standardizzati
                batch_gradient[0] = [batch_gradient[0][i] + current_gradient[i] for i in range(self.depth + 1)]
            for i in range(self.depth):
                self.hidden_layers[i].weight_matrix += (batch_gradient[0][i] * eta / len(X)) - batch_gradient[1][i]
            self.output_layer.weight_matrix += (batch_gradient[0][self.depth] * eta / len(X)) - batch_gradient[1][-1]
        if plot:
            self.plot_error(errors, validation_errors, "training_error")
            self.plot_output(X_stand, y, "Training set")
            if validation:
                self.plot_output(validation_input_stand, validation[1], "Validation set")

    def K_fold_CV(self, X, y, fold_number = 4):
        VL_input_portions = [X.iloc[i::fold_number] for i in range(fold_number)]
        VL_target_portions = [y.iloc[i::fold_number] for i in range(fold_number)]
        store_VL_errors = np.zeros(fold_number)
        for i in range(fold_number):
            TR_input_portion = X[~X.index.isin(VL_input_portions[i].index)]
            TR_target_portion = y[~y.index.isin(VL_input_portions[i].index)]
            validationK = [VL_input_portions[i],VL_target_portions[i]]
            self.backpropagation_batch(TR_input_portion, TR_target_portion, validationK)
            current_VL_error = self.LED_regression(validationK[0], validationK[1], True)
            print(f"Errore sul {i+1}º validation set: {current_VL_error}")
            store_VL_errors[i] = current_VL_error
            mean_VL_error = np.sum(store_VL_errors)/fold_number
            self.reset(self)
        print(f"Errore medio su tutti le {fold_number} fold: {mean_VL_error}")
        return mean_VL_error
            
    def backpropagation_online(self, X, y):
        for index, row in X.iterrows():
            current_gradient = self.backpropagation_iteration(row, y.iloc[index])
            for i in range(self.depth):
                self.hidden_layers[i].weight_matrix += current_gradient[i]
            self.output_layer.weight_matrix += current_gradient[self.depth]

    def backpropagation_iteration(self, x, y):
        #calcolo dell'output continuo della rete
        output = self.network_output(x)
        #inizializzazione della matrice contenente i gradienti di tutti i pesi della rete
        store_gradient = []
        store_output_delta = []
        #calcolo del delta dell'output layer (in questo caso della singola output unit)
        output_layer_der = self.output_layer.der_act(self.store_hidden_result[-1])
        store_output_delta = (y - output) * output_layer_der
        #inizializzione della matrice contenente i grandienti dei pesi dell'output layer
        #aggiungo il risultato del bias al vettore degli output dell'ultimo hidden layer
        updated_hidden_result = np.concatenate((np.array([1]), self.store_hidden_result[self.depth - 1]))
        #inizio a iterare sugli output neruons
        #aggiunta alla matrice totale dei gradienti la matrice dei gradienti dell'output layer
        store_gradient.append(np.outer(store_output_delta, updated_hidden_result))

        if (self.depth == 1):
            current_hidden_layer = self.hidden_layers[0]
            store_current_hidden_layer_delta = np.zeros(current_hidden_layer.neurons)
            #inizializzo la matrice che conterrà i gradienti dei pesi dell' hidden layer più vicino all'output layer
            updated_hidden_result = np.concatenate((np.array([1]), x))
            #itero sui neuroni del layer corrente
            current_hidden_layer_der = current_hidden_layer.der_act(x)
            for index_neuron in range(current_hidden_layer.neurons):
                #calcolo il prodotto scalare tra il vettore contenente il delta del layer più a destra e il vettore contenente i pesi 
                #di ogni neurone del layer più a destra che li collegano all'index_neuronesimo neurone
                #aggiungo alla matrice contenente i delta del layer corrente il prodotto di counter e la derivata della funzione di attivazione
                #applicata alla net delle uscite dei neuroni precedenti
                store_current_hidden_layer_delta[index_neuron] = np.dot(store_output_delta, self.output_layer.weight_matrix[:,index_neuron + 1]) * current_hidden_layer_der[index_neuron]
                #itero sui pesi dei singoli nueroni del layer corrente
            store_gradient.append(np.outer(store_current_hidden_layer_delta, updated_hidden_result))
            #inverto l'ordine della matrice contenente i gradienti di ogni peso in modo da avere prima i gradienti del primo hidden layer
            # e dopo i gradienti dell'output layer 
            store_gradient.reverse()
            return store_gradient

        #passiamo a valutare i gradienti dell' hidden layer più vicino all'output layer
        current_hidden_layer = self.hidden_layers[self.depth - 1]
        #inizializzo il vettore contenente i delta dell' hidden layer più vicino all'output layer
        store_current_hidden_layer_delta = np.zeros(current_hidden_layer.neurons)
        #inizializzo la matrice che conterrà i gradienti dei pesi dell' hidden layer più vicino all'output layer
        #aggiungo il bias
        updated_hidden_result = np.concatenate((np.array([1]), self.store_hidden_result[self.depth - 2]))
        #itero sui neuroni del layer
        current_hidden_layer_der = current_hidden_layer.der_act(self.store_hidden_result[self.depth - 2])
        for index_neuron in range(current_hidden_layer.neurons):
            #nella matrice contenente i delta di questo layer metto il prodotto del delta dell'output layer (in questo caso un solo neurone) 
            #per il peso che va da index_neuron all'output neuron per la derivata della funzione di attivazione applicata alla net del neurone
            store_current_hidden_layer_delta[index_neuron] = np.dot(store_output_delta, self.output_layer.weight_matrix[:,index_neuron+1]) * current_hidden_layer_der[index_neuron]
            #itero sul numero di pesi del layer corrente
        store_gradient.append(np.outer(store_current_hidden_layer_delta, updated_hidden_result))

        #aggiorniamo il valore del delta del prossimo layer con il valore del delta dell'ultimo hidden layer
        next_layer_delta = store_current_hidden_layer_delta

        #comincio a iterare partendo dal penultimo hidden layer fino ad arrivare al secondo hidden layer con passo -1
        for hidden_layer_index in range(self.depth - 2, 0, -1):
            #setto l'hidden layer corrente
            current_hidden_layer = self.hidden_layers[hidden_layer_index]
            #inizializzo l'array che conterrà i delta dei neuroni di questo layer 
            store_current_hidden_layer_delta = np.zeros(current_hidden_layer.neurons)
            #inizializzo la matrice che conterrà gli aggiornamenti dei pesi dei neuroni di questo layer
            #aggiungo il bias ai neuroni del layer più vicino all'input layer
            updated_hidden_result = np.concatenate((np.array([1]), self.store_hidden_result[hidden_layer_index - 1]))
            #itero sul numero di neuroni di questo layer
            current_hidden_layer_der = current_hidden_layer.der_act(self.store_hidden_result[hidden_layer_index - 1])
            for index_neuron in range(current_hidden_layer.neurons):
                #calcolo il prodotto scalare tra il vettore dei delta dei neuroni del layer più a destra per il vettore contenente i pesi 
                #di ogni neurone del layer più a destra che li collegano all'index_neuronesimo neurone
                #calcolo il prodotto di counter per la derivata della funzione di attivazione del layer corrente applicata
                #ai risultati del layer più a sinistra
                store_current_hidden_layer_delta[index_neuron] = np.dot(next_layer_delta, self.hidden_layers[hidden_layer_index + 1].weight_matrix[:,index_neuron + 1]) * (current_hidden_layer.der_act(self.store_hidden_result[hidden_layer_index - 1])[index_neuron])
                #itero sui singoli pesi del layer corrente
            store_gradient.append(np.outer(store_current_hidden_layer_delta, updated_hidden_result))
            #aggiorno il next_layer_delta in modo che il delta del layer corrente valga come delta del layer successivo per il layer
            #che considero alla prossima iterazione 
            next_layer_delta = store_current_hidden_layer_delta

        #considero l'ultimo hidden layer, ossia quello a sinistra dell'input layer
        current_hidden_layer = self.hidden_layers[0]
        #inizializzo la matrice che conterrà i delta di questo layer
        store_current_hidden_layer_delta = np.zeros(current_hidden_layer.neurons)
        #inizializzo la matrice che conterrà gli aggiornamenti dei pesi di questo layer
        #aggiungo il bias ai neuroni del layer più a sinistra (l'input layer)
        updated_hidden_result = np.concatenate((np.array([1]), x))
        #itero sui neuroni del layer corrente
        current_hidden_layer_der = current_hidden_layer.der_act(x)
        for index_neuron in range(current_hidden_layer.neurons):
            #calcolo il prodotto scalare tra il vettore contenente il delta del layer più a destra e il vettore contenente i pesi 
            #di ogni neurone del layer più a destra che li collegano all'index_neuronesimo neurone
            #aggiungo alla matrice contenente i delta del layer corrente il prodotto di counter e la derivata della funzione di attivazione
            #applicata alla net delle uscite dei neuroni precedenti
            store_current_hidden_layer_delta[index_neuron] = np.dot(next_layer_delta, self.hidden_layers[1].weight_matrix[:,index_neuron + 1]) * current_hidden_layer_der[index_neuron]
            #itero sui pesi dei singoli nueroni del layer corrente
            #aggiungo la matrice appena calcolata alla matrice totale
        store_gradient.append(np.outer(store_current_hidden_layer_delta, updated_hidden_result))
        #inverto l'ordine della matrice contenente i gradienti di ogni peso in modo da avere prima i gradienti del primo hidden layer
        # e dopo i gradienti dell'output layer 
        store_gradient.reverse()
        return store_gradient

def grid_search(training_data, validation_data, activation_function, max_layer_size = 7, hidden_units = [5, 50], eta = [-3, -1], lambda_tichonov = [-3, -1], alpha = [0, 0.5], K_fold=False):
    hidden_units_range = np.linspace(hidden_units[0], hidden_units[1], hidden_units[1] // hidden_units[0])
    eta_range = np.logspace(eta[0], eta[1], num = 3, base = 10)
    lambda_tichonov_range = np.logspace(lambda_tichonov[0], lambda_tichonov[1], 3)
    alpha_range = np.logspace(alpha[0], alpha[1], num = 3, base = 10)
    best_model = [0, 0, 0, 0]
    best_validation_error = np.inf
    for current_hidden_units_number in hidden_units_range:
        hidden_layer_number = (int(current_hidden_units_number) // max_layer_size) + 1
        hidden_layer_units = [hidden_units[0]]
        for i in range(hidden_layer_number // 2):
            hidden_layer_units.append(min(hidden_layer_units[-1] + 1, max_layer_size))
        for i in range(hidden_layer_number // 2, hidden_layer_number - 1):
            hidden_layer_units.append(max(hidden_layer_units[-1] - 1, training_data[1].shape[1]))
        hidden_layer_units.append(training_data[1].shape[1])
        hidden_activation_function = [activation_function] * hidden_layer_number
        hidden_activation_function.append(Id())
        current_model = Network(0.5, hidden_layer_number, training_data[0].shape[1], hidden_layer_units, hidden_activation_function)
        for current_eta in eta_range:
            for current_lambda_tichonov in lambda_tichonov_range:
                for current_alpha in alpha_range:
                    print(f"Numero di neuroni: {current_hidden_units_number}")
                    print(f"Eta: {current_eta}")
                    print(f"Lambda: {current_lambda_tichonov}")
                    print(f"Alpha: {current_alpha}")
                    if K_fold:
                        current_validation_error = current_model.K_fold_CV(training_data[0], training_data[1], batches_number = 10, eta = current_eta, lambda_tichonov=current_lambda_tichonov, alpha = current_alpha, plot=False)
                    else:
                        current_model.backpropagation_batch(training_data[0], training_data[1], batches_number = 100, eta = current_eta, lambda_tichonov=current_lambda_tichonov, alpha = current_alpha, validation = validation_data)
                        current_validation_error = current_model.LED_regression(validation_data[0], validation_data[1], mean=True)
                    
                    if current_validation_error < best_validation_error:
                        best_model = [current_hidden_units_number, current_eta, current_lambda_tichonov, current_alpha]
                        best_validation_error = current_validation_error
                    current_model.reset()

    return best_model, best_validation_error