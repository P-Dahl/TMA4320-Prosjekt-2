import numpy as np
from utils import onehot

class Layer:

    """
    Base class for layers in the neural network with forward and backward pass.
    """
    def __init__(self):
        
        return

    def forward(self,inputs):
        raise NotImplementedError

    def backward(self,grad):
        raise NotImplementedError
    
    def step_Adam(self, alpha, beta1=0.9, beta2=0.999, epsilon=1e-8):

        M = {}
        V = {}
        t = 0
        
        for param in self.params:
            M[param] = np.zeros_like(self.params[param]['w'])
            V[param] = np.zeros_like(self.params[param]['w'])

        for param in self.params:
            t += 1
            G = self.params[param]['d']
            
            M[param] = beta1 * M[param] + (1 - beta1) * G
            
            V[param] = beta2 * V[param] + (1 - beta2) * (G ** 2)
            
            M_hat = M[param] / (1 - beta1 ** t)
            
            V_hat = V[param] / (1 - beta2 ** t)
            
            #Prøver å oppdatere Params likt som i step_dg
            self.params[param]['w'] -= alpha * M_hat / (np.sqrt(V_hat) + epsilon)

    
    def step_gd(self,alpha):
    
        """
        Performs a gradient descent step given learning rate.
        Assumes that the layer has a parameter dictionary "params" on the form

        params = {
            'w1': {         
                'w': w,         The parameter matrix
                'd': d,         The gradient of loss wrt the parameter matrix
                },
            'w2': {....},
            
        }
        where each parameter has a key 'w' for weights and 'd' for gradients.
        """
        for param in self.params:
            self.params[param]['w'] -= alpha*self.params[param]['d']




class Attention(Layer):

    def __init__(self, d, k):
        #definerer parametermatrisene Wq Wk som tilfeldige variabler
        self.Wq = np.random.randn(d,k)*0.1
        self.Wk = np.random.randn(d,k)*0.1

        #definerer nødvendige variabler
        self.d = d
        self.k = k

        #definerer nødvendige lag innad i attention laget
        self.softmax = Softmax()
        self.Wo = LinearLayer(k, d)
        self.Wv = LinearLayer(k, d)

        self.params = {
            'wq':{
                'w' : self.Wq,
                'd' : np.zeros_like(self.Wq)
            },
            'wk':{
                'w' : self.Wk,
                'd' : np.zeros_like(self.Wk)
            },
        }
    
        return

        

    def forward(self,z):
        self.z = z

        #definerer matrisen, B, som skal gis til softmax
        B = np.transpose(self.z)@np.transpose(self.Wq)@self.Wk@self.z

        #setter nedre triangularen til B til -inf
        i1, i2 = np.tril_indices(self.k,-1)
        B[i1,i2] -= np.inf

        self.A = self.softmax.forward(B)

        return self.z + self.Wo.forward(self.Wv.forward(self.z@self.A))


    def backward(self,grad):
        self.grad = grad

        g_ov = self.Wv.backward(self.Wo.backward(self.grad))

        g_s = self.softmax.backward(np.transpose(self.z)@g_ov)

        #regner ut deriverte mhp parameterene, lagrer disse
        self.params['wk']['d'] = self.Wq@self.z@g_s@np.transpose(self.z)
        self.params['wq']['d'] = self.Wk@self.z@np.transpose(g_s)@np.transpose(self.z)

        return self.grad + g_ov@np.transpose(self.A) + np.transpose(self.Wk)@self.Wq@self.z@np.tranpose(g_s)
    
    #definerer egen step_gd funksjon
    def step_gd(self, alpha):
        self.Wo.step_gd(alpha)
        self.Wv.step_gd(alpha)

        #kjører originale step_gd funksjonen fra layers
        super.step_gd(alpha)



class Softmax(Layer):

    def __init__(self):
        
        return

    
    def forward(self,z):

        self.P = np.exp(z-z.max(axis = 1, keepdims = True))
        self.Q = np.sum(self.P, axis = 1, keepdims = True)
        
        self.z_l = np.divide(self.P, (self.Q + 10e-8))
        self.z = z
        return self.z_l


    def backward(self,g_l):
        
        S = np.divide(self.P,(np.multiply(self.Q,self.Q)+10e-8))
        delLdelZ = np.multiply(g_l,self.z_l) - np.multiply(np.sum((np.multiply(g_l,S)), axis = 1, keepdims = True),self.P)
        self.delLdelZ = delLdelZ
        return delLdelZ



class CrossEntropy(Layer):

    def __init__(self):
        """
        Your code here
        """
        return

        

    def forward(self,Z,y):

        self.y = y
        self.Z = Z

        #Definerer størrelser på dimensjoner
        self.m = Z.shape[0]
        self.n = Z.shape[1]

        #Definerer 
        self.p = np.ones(self.m)@(np.multiply(Z,onehot(y,self.m)))
        self.q = -np.log(self.p)

        self.L = (1/self.n)*np.sum(self.q)
        
        return self.L


    def backward(self):
        
        self.grad_Z = -(1/self.n)*(np.divide(onehot(self.y, self.m),(self.Z + 10e-8)))

        return self.grad_Z
    


class LinearLayer(Layer):

    """
    Linear Layer
    """
    def __init__(self,input_size, output_size,init_scale = 0.1):
        """
        Constructor takes input size and output size of layer 
        and scale for the weights
        """

        #Initialize weights using a sample from the normal distribution
        #scaled with the init_scale
        self.w = np.random.randn(output_size,input_size)*init_scale
        self.params = {"w":{'w':self.w,
                            'd':np.zeros_like(self.w)}}
        

    def forward(self,x):
        """
        Computes the affine transformation of the forward pass
        Stores input for backwards pass and returns output y = Wx.

        x: input, array of shape (batch_size, input_size, n) = (b,d,n)
        y: output, array of shape (batch_size, output_size, n) = (b,o,n)
        """

        self.x = x
        
        #Return output of layer
        #y = w@x
        y = np.einsum('od,bdn->bon',self.params['w']['w'],x)
        return y
        
    def backward(self,grad):
        """
        Performs backward pass.

        grad: gradient of loss wrt output of layer, shape (batch_size, output_size, n) = (b,o,n)
        """

        b = grad.shape[0]

        #Compute gradient (average over B batches) of loss wrt weight w: 
        #dL/dw = (1/B)*sum_b^B (grad_b@x_b^T)
        self.params['w']['d'] = np.einsum('bon,bdn->od',grad,self.x)/b

        #Return gradient of loss wrt input of layer
        #dL/dw = w@grad.T
        return np.einsum('od,bon->bdn',self.params['w']['w'],grad)
    

class Relu(Layer):
    """
    Relu activation function
    """

    def __init__(self):
        return

    def relu(self,x):
        #relu(x) = max(0,x)
        return np.maximum(np.zeros(x.shape), x)

    def forward(self,x):
        
        #Store input for backwards pass
        self.x = x
        return self.relu(x)

    def backward(self,grad):

        #dL/dx = grad * relu'(x)
        return grad * np.where(self.x > 0, np.ones_like(self.x), np.zeros_like(self.x))



class EmbedPosition(Layer):
    def __init__(self,n_max,m,d,init_scale=1e-1):   

        """
        n_max: maximum length of input sequence
        m: number of items in the vocabulary / number of integers
        d: embedding dimension
        """

        #Initialize a linear layer for the embedding
        self.embed = LinearLayer(m,d,init_scale)
        #Initialize the position embedding matrix
        self.w = np.random.randn(d,n_max)*init_scale

        #Initialize the parameter dictionary for weight with key "Wp"
        self.params = {"Wp":{'w':self.w,'d':None}}

    def forward(self,X):

        """
        Input:
            X: one-hot encoded array of shape (b,m,n).

        Output:
            z_0: array of shape (b,d,n)

        embed.forward(X) maps (b,m,n) to (b,d,n). 
        Assigns a column of size d to each integer in the sequence
        and add positional embedding matrix (params['Wp']['w'][:,:n]) (b,d,n).

        Equivalent to 

        z_0 = W_E@X + W_P[:,:n]

        """

        #We assume that n < n_max
        n = X.shape[-1]
        z_0 = self.embed.forward(X) + self.params['Wp']['w'][:,:n]
        return z_0
    
    def backward(self,grad):
        """
        Input:
            - grad of shape (b,d,n)

        Output:
            - None
        """

        
        b = grad.shape[0]

        #Compute gradient (average over B batches) of loss wrt positional embedding w:
        self.params['Wp']['d'] = np.zeros_like(self.w)
        self.params['Wp']['d'] += np.sum(grad,axis=0)/b

        #Use backwards pass of the linear layer
        self.embed.backward(grad)

        #This is always the final layer, so we return None
        return None
    
    def step_gd(self,step_size):

        #We need to call the step_gd method of the linear layer
        self.embed.step_gd(step_size)

        #And since we override step_gd(), we use super 
        #which calls the step_gd() of the base class
        #and does gd for the paramters in the params dict
        super().step_gd(step_size)




class FeedForward(Layer):


    def __init__(self,d, p,init_scale = 0.1):
        """
        Input:
            d: input dimension of first layer and output of second
            p: output dimension of first and input of second.

        """

        #first linear layer with input size d and output size p
        self.l1 = LinearLayer(d,p,init_scale)

        #We use the Relu activation function
        self.activation = Relu()

        #second linear layer with input size p and output size d
        self.l2 = LinearLayer(p,d,init_scale)


    def forward(self,x):
        """
        Input:
            - x of shape (b,d,n)
        Output:
            - shape (b,d,n)

        This is equivalent to
        y = x + W2.T@Relu(W1@x)

         (W1,W2 are p x d)
        """

        self.x = x

        return x + self.l2.forward(self.activation.forward(self.l1.forward(x)))
    
    def backward(self,grad):
        """
        Input:
            - grad of shape (b,d,n)

        Output:
            - derivative of loss wrt input x. Shape (b,d,n)
        
        """

        #We use backward pass of the linear layers and activation.
        #Recall that the backward pass reverse the order of the layers. 
        grad_feed_forward = self.l1.backward(self.activation.backward(self.l2.backward(grad)))

        #Since forward pass is x + W2.T@Relu(W1@x)
        return grad + grad_feed_forward


    def step_gd(self,step_size):

        #Call the step_gd method of the linear layers
        self.l1.step_gd(step_size)
        self.l2.step_gd(step_size)