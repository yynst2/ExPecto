"""Training a ExPecto sequence-based expression model.

This script takes an expression profile, specified by the expression values
in the targetIndex-th column in the expFile. The expression values can be log
RPKM from RNA-seq, log CAGE count, or microarray normalized scores. The rows
of the inputFile must match with the genes or TSSes specified in
./resources/geneanno.csv.

Example:
        $ python ./train.py --expFile ./resources/geneanno.exp.csv --targetIndex 1 --output model.adipose


"""
import argparse
import xgboost as xgb
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
import h5py

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--expFile', action="store", dest="expFile")
parser.add_argument('--targetIndex', action="store", dest="targetIndex",type=int)
parser.add_argument('--output', action="store", dest="output")
parser.add_argument('--inputFile', action="store", dest="inputFile",default='./resources/Xreducedall.2002.npy')
parser.add_argument('--pseudocount', action="store", dest="pseudocount", type=float, default=0.0001)
parser.add_argument('--num_round', action="store", dest="num_round", type=int, default=100)
parser.add_argument('--l2', action="store", dest="l2", type=float, default=100)
parser.add_argument('--l1', action="store", dest="l1", type=float, default=0)
parser.add_argument('--eta', action="store", dest="eta", type=float, default=0.01)
parser.add_argument('--base_score', action="store", dest="base_score", type=float, default=2)
parser.add_argument('--threads', action="store", dest="threads", type=int, default=16)

args = parser.parse_args()
Xreducedall = np.load(args.inputFile)

geneanno = pd.read_csv('./resources/geneanno.csv')
geneexp = pd.read_csv(args.expFile)

trainind  = np.asarray(geneanno['seqnames']!='chrX') * np.asarray(geneanno['seqnames']!='chrY')  *  np.asarray(geneanno['seqnames']!='chr8' )
testind =  np.asarray(geneanno['seqnames']=='chr8' )

dtrain = xgb.DMatrix(Xreducedall[trainind ,:])
dtest = xgb.DMatrix(Xreducedall[(testind) ,:])


dtrain.set_label(np.asarray(np.log(geneexp.iloc[trainind , args.targetIndex]+ args.pseudocount)))
dtest.set_label(np.asarray(np.log(geneexp.iloc[(testind), args.targetIndex]+ args.pseudocount)))

param = {'booster':'gblinear','base_score':args.base_score, 'alpha':0,
    'lambda':args.l2, 'bst:eta':args.eta,'objective':'reg:linear',
    'nthread':args.threads ,"early_stopping_rounds":10}

evallist  = [(dtest,'eval'), (dtrain,'train')]
num_round = args.num_round
bst = xgb.train( param, dtrain, num_round, evallist )
ypred = bst.predict(dtest)

bst.save_model(args.output+'.pseudocount'+str(args.pseudocount)+'.lambda'+str(args.l2)+'.round'+str(args.num_round)+'.basescore'+str(args.base_score)+'.'+geneexp.columns[args.targetIndex]+'.save')
bst.dump_model(args.output+'.pseudocount'+str(args.pseudocount)+'.lambda'+str(args.l2)+'.round'+str(args.num_round)+'.basescore'+str(args.base_score)+'.'+geneexp.columns[args.targetIndex]+'.dump')
