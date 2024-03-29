#!/usr/bin/env python3

import numpy
import sys

import logging

logging.basicConfig(level=logging.ERROR)#,filename="logwitheverything.txt")

numpy.seterr(over="ignore")
#seed=int(sys.argv[5])
seed=1023    # For random shuffling since I have to split for validation set
numpy.random.seed(seed)

class LogisticRegression(object):

    def __init__(self,alpha=0.001,l=0.001):
        self.alpha=alpha # Learning rate
        self.l=l # Regularisation parameter
        self.W=None
        self.b=None

    def __sigmoid(self,X):
        return numpy.clip(1.0/(1.0+numpy.exp((-1)*(X))),0.000001,0.999999) # Clipping to avoid sigmoid saturation.

    def __cost(self,h,y):
        cost=numpy.dot((-1)*y.T,numpy.log(h))-numpy.dot((1-y).T,numpy.log(1-h)) # For early stopping criteria
        print(cost.shape)
        sys.exit()

    def __output(self,X):
        return numpy.dot(X,self.W)+self.b

    def __gradient(self,h,y,X):
        return numpy.dot(X.T,(h-y))+((self.l/2)*self.W) # regularised gradient

    def predict(self,X):
        output=self.__sigmoid(self.__output(X))
        return (output[:]>0.5) # predicts boolean outputs

    def accuracy(self,h,y):
        total=y.shape[0]
        result=numpy.hstack((h,y))
        right=result[result[:,0]==result[:,1]].shape[0]
        return float(right)/float(total)

    def fit(self,X,y):
        feature_dim=X.shape[1]
        y=y[:,numpy.newaxis]
        train_X,train_y,test_X,test_y=self.create_train_test(X,y) # Not really a test set. Using it for validation.
        self.W=numpy.zeros(shape=(feature_dim,1))
        self.b=numpy.zeros(shape=(1,))
        epoch=1
        min_cost=0.0 # For storing minimum cost and detect increase in validation error in case of overfitting.
        prev_grad=0 # For momentum
        patience=5 # early stopping
        while epoch:
            output=self.__sigmoid(self.__output(train_X)) 
            cost=self.__cost(output,train_y) # Cost on training iteration
            val_cost=self.__cost(self.__sigmoid(self.__output(test_X)),test_y) # Cost on validation set
            if val_cost > min_cost and epoch != 1:
                logging.info("Skipping weight backup.")
                logging.info("Decreasing patience and alpha.")
                self.alpha*=0.1 # Learning rate decay
                patience-=1
                logging.info("Replacing with previous backup.")
                self.W=prev_W # weight roll back 
            else:
                min_cost=val_cost
                prev_W=self.W
            #logging.debug("prev {} now {}".format(prev_cost,val_cost))
            if self.alpha < 0.000001 or epoch > 10000 or patience == 0:
                logging.info("Restoring backup weights")
                self.W=prev_W # Restore weights for minimum error and exit.
                accuracy=self.accuracy(self.predict(test_X),test_y)
 #               logging.error("Epoch {} error {}. Training error {}. Accuracy {}".format(epoch,val_cost,cost,accuracy))
                break
            grad=self.__gradient(output,train_y,train_X)
            self.b=self.b-(self.alpha*numpy.mean(output-train_y))
            self.W=self.W-(self.alpha*grad)-(0.9*prev_grad)
            prev_grad=self.alpha*grad
            if epoch % 100 == 0:
                accuracy=self.accuracy(self.predict(test_X),test_y)
                logging.info("Epoch {} error {}. Training error {}. Accuracy {}".format(epoch,val_cost,cost,accuracy))
#            if epoch % 1000 == 0:
#                self.alpha=0.0001
#            if epoch % 5000 == 0:
#                self.alpha=0.00001

            epoch+=1

    def create_train_test(self,X,y,split=0.1):
        dataset=numpy.hstack((X,y))
        numpy.random.shuffle(dataset)
        split_ind=int(split*X.shape[0])
        test_set=dataset[:split_ind]
        train_set=dataset[split_ind:]
        train_X,train_y=numpy.split(train_set,[-1],axis=1) 
        test_X,test_y=numpy.split(test_set,[-1],axis=1)
        return train_X,train_y,test_X,test_y


def load_data(filename):
    return numpy.loadtxt(filename,dtype=numpy.uint32,delimiter=" ")

def get_doc_data(data_set,doc_id):
    return data_set[data_set[:,0]==doc_id]

def create_feature_vector(word_counts,max_len):
    vector=numpy.zeros(max_len)
    for word_count in word_counts:
        try:
            vector[word_count[1]]=word_count[2]
        except:
            pass
            #vector[-1]=word_count[2]
    #logging.debug("{}".format(vector[vector != 0].shape))
    return vector

def scale(X):
    return X/(1+numpy.max(X))

def tf(X):
    num_docs=numpy.apply_along_axis(lambda x:x[x!=0].shape[0],0,X)+1
    idf=numpy.log(X.shape[0]/num_docs)
    tf=numpy.apply_along_axis(lambda x:x/numpy.max(x),1,X)
    return tf*idf

def get_dataset(filename,enforce=None):
# load dataset
    logging.info("Loading data.")
    data=load_data(filename)
    logging.info("Data loaded.")
# get word count for each document
    doc_features=list()
    logging.info("Extracting features.")
    for i in numpy.unique(data[:,0]):
        doc_words=get_doc_data(data,i)
        #logging.debug("{}".format(doc_words))
        doc_features.append((i,doc_words))
    logging.info("Features extracted.")
    
# construct dataset matrix
    vectors=list()
    logging.info("Creating vectors.")
    if enforce == None:
        for _id,features in doc_features:
            vectors.append(create_feature_vector(features,numpy.max(data[:,1])+2)) # +1 to compensate for off by one and +1 to account for unseen words.
    else:
        for _id,features in doc_features:
            vectors.append(create_feature_vector(features,enforce[1])) 
    logging.info("Vectors created.")
    logging.info("Collecting to dataset matrix.")
    X=numpy.array(vectors)
    #X=(X-numpy.mean(X))/(1+numpy.var(#X))
    #X=numpy.apply_along_axis(scale,0,X)
    #print(X)
    return tf(X) # returns tf idf of the document matrix

if __name__=="__main__":

# load dataset
    logging.info("Loading data.")
    X=get_dataset(sys.argv[1])
    enforce_shape=X.shape
    logging.info("Data loaded.")
    labels=load_data(sys.argv[2])
    #print(labels[labels==0].shape[0]/labels.shape[0])
    #print(X)
    #print(tfidf(X))
    #X=tf(X)
    #sys.exit()
# learn
    LR=LogisticRegression(alpha=0.01)
    LR.fit(X,labels)
    logging.info("Beginning test.")
    X_test=get_dataset(sys.argv[3],enforce_shape)
#    y_test=load_data(sys.argv[4])
#    logging.error("Testing set accuracy is {} for seed {}".format(LR.accuracy(LR.predict(X_test),y_test[:,numpy.newaxis]),seed))
    out=LR.predict(X_test)
    for i in out[:,0]:
        print(int(i))
        pass
