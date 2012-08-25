#!/usr/bin/env python
import roslib; roslib.load_manifest("hadjective_train_pipe")
import rospy
import numpy as np
import sys 
import os
from optparse import OptionParser
import cPickle
import bolt_learning_utilities as utilities
import extract_features as extract_features
import matplotlib.pyplot as plt 
import sklearn.decomposition

from bolt_feature_obj import BoltFeatureObj
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.metrics import classification_report
from sklearn.datasets.samples_generator import make_blobs
from sklearn.neighbors import KNeighborsClassifier
from sklearn import cross_validation

# Loads the data from h5 table and adds labels
# Returns the dictionary of objects
def loadDataFromH5File(input_file, adjective_file):
   
    # Takes the input h5 file and converts into bolt object data
    all_bolt_data = utilities.convertH5ToBoltObjFile(input_file, None, False);
   
    # Inserts adjectives into the bolt_data  
    all_bolt_data_adj = utilities.insertAdjectiveLabels(all_bolt_data, "all_objects_majority4.pkl", adjective_file, True)

    return all_bolt_data_adj


# Takes the bolt data and extracts features to run
def BoltMotionObjToFeatureObj(all_bolt_data):
    """
    Pull out PCA components from all data

    For each object - pull out features and store in feature_obj
    with the same structure as all_bolt_data
   
        Dictionary - "tap", "slide", "slow_slide", 
                     "thermal_hold", "squeeze"

    """
    # DO PCA Calculations here 
    
    # Store in feature class object
    all_features_obj_dict = dict();

    for motion_name in all_bolt_data:
        motion_list = all_bolt_data.get(motion_name)
        print motion_name

        feature_list = list()
        # For all objects
        for motion in motion_list:
            
            bolt_feature_obj = extract_features.extract_features(motion)
            
            feature_list.append(bolt_feature_obj)

        # Store all of the objects away
        all_features_obj_dict[motion_name] = feature_list
            
    return all_features_obj_dict        
    

def bolt_obj_2_feature_vector(all_bolt_data, feature_name_list):
    """
    Pull out PCA components from all data

    For each object - pull out features and store in feature_obj
    with the same structure as all_bolt_data
   
        Dictionary - "tap", "slide", "slow_slide", 
                     "thermal_hold", "squeeze"

    Directly store the features into a vector
    See createFeatureVector for more details on structure

    """
    
    # DO PCA Calculations here 
     


    # Store in feature class object
    all_features_vector_dict = dict()
    
    # Store labels
    for motion_name in all_bolt_data:
        motion_list = all_bolt_data.get(motion_name)
        print motion_name

        all_adjective_labels_dict = dict()
        feature_vector_list = list()
        # For all objects
        for motion in motion_list:
            #import pdb; pdb.set_trace() 
            # Create feature vector
            bolt_feature_obj = extract_features.extract_features(motion)
            feature_vector = utilities.createFeatureVector(bolt_feature_obj, feature_name_list) 
            feature_vector_list.append(feature_vector)

            # Create label dictionary
            labels = motion.labels
            for adjective in labels:
                # Check if it is the first time adjective added
                if (all_adjective_labels_dict.has_key(adjective)):
                    adjective_array = all_adjective_labels_dict[adjective]
                else:
                    adjective_array = list()
                
                # Store array
                adjective_array.append(labels[adjective])
                all_adjective_labels_dict[adjective] = adjective_array

        # Store all of the objects away
        all_features_vector_dict[motion_name] = np.array(feature_vector_list)
     
    return (all_features_vector_dict, all_adjective_labels_dict)      


def run_dbscan(input_vector, num_clusters):
    """
    run_dbscan - expects a vector of features and the number of
                 clusters to generate

                 dbscan uses nearest neighbor metrics to compute
                 similarity

    Returns the populated clusters
    """


def run_kmeans(input_vector, num_clusters, obj_data):
    """
    run_kmeans - expects a vector of features and the number of
                 clusters to generate

    Returns the populated clusters 
    """
    k_means = KMeans(init='k-means++', k=num_clusters, n_init=100)

    k_means.fit(input_vector)
    k_means_labels = k_means.labels_
    k_means_cluster_centers = k_means.cluster_centers_
    k_mean_labels_unique = np.unique(k_means_labels)

    # Pull clusters out
    clusters = dict()
    cluster_names = dict()
    cluster_ids = dict()
    cluster_all_adjectives = dict()
    # Get a list of all adjectives
    adjectives = obj_data[0].labels.keys()

    
    for labels in k_mean_labels_unique:
        idx = np.nonzero(k_means_labels == labels)
        clusters[labels] = [obj_data[i] for i in idx[0]]
        cluster_names[labels] = [obj.name for obj in clusters[labels]]
        cluster_ids[labels] = [obj.object_id for obj in clusters[labels]]
   
    for adj in adjectives:
        cluster_adj = dict()
        for labels in k_mean_labels_unique:
            cluster_adj[labels] = [obj.labels[adj] for obj in clusters[labels]] 
        
        cluster_all_adjectives[adj] = cluster_adj

    import pdb; pdb.set_trace() 
    
    return (k_means_labels, k_means_cluster_centers, clusters)


def train_knn(train_vector, train_labels, test_vector, test_labels, N):
    """
    train_knn - expects a vector of features and a nx1 set of
                corresponding labels.  Finally the number of
                neighbors used for comparison

    Returns a trained knn classifier
    """
    #import pdb; pdb.set_trace()
    knn = KNeighborsClassifier(n_neighbors = N, weights='uniform')
    knn.fit(train_vector, train_labels)

    import pdb; pdb.set_trace()
    knn_score = knn.score(test_vector, test_labels)
    knn_predict = knn.predict(test_vector)
    knn_comparison = knn_predict - test_labels

    report = classification_report(test_labels, knn_predict, labels=None, target_names = None)
    print report

    return(knn_score, knn_predict, knn_comparison)


def true_false_results(predicted_labels, true_labels):

    FP = (predicted_labels - true_labels).tolist().count(1)
    FN = (predicted_labels - true_labels).tolist().count(-1)
    TP = (predicted_labels & true_labels).tolist().count(1)
    TN = ((predicted_labels | true_labels) ^ True).tolist().count(1)


    return(TP, TN, FP, FN)


def mattews_corr_coef(TP,TN,FP,FN):
    
    try:
        MCC = (TP*TN - FP*FN)/(np.sqrt(((TP+FP)*(TP+FN)*(TN+FP)*(TN+FN))))
    except:
        MCC = (TP*TN - FP*FN)/1

    return MCC


def train_svm(train_vector, train_label):
    """
    train_svm - expects a vector of features and a nx1 set of
                corresponding labels

    Returns the a trained SVM classifier
    """



# MAIN FUNCTION
def main(input_file, adjective_file):
 
    # Load data into the pipeline, either from an h5 and adjective
    # File or directly from a saved pkl file
    print "Loading data from file"
    if input_file.endswith(".h5"):
        all_data = loadDataFromH5File(input_file, adjective_file)
    else:
        all_data = utilities.loadBoltObjFile(input_file)

    print "loaded data"

    import pdb;pdb.set_trace()
   
    all_knn_results = dict()

    #If the input is a single pickle file
    #for i in range (36)
    #adjective_name = all_data['squeeze'][0].labels.keys()[i]
    #all_knn_results[adjective_name] = dict()
    #for motion_name in all_data.get(motion_name)
    #all_knn_results[adjective].motion_name = []
   

    # Split the data into train and test
    train_data, test_data = utilities.split_data(all_data, 0.9)
    
    # Take loaded data and extract out features
    feature_name_list = ["gripper_close"]
    train_feature_vector, train_adjective_dictionary = bolt_obj_2_feature_vector(train_data, feature_name_list)
    test_feature_vector, test_adjective_dictionary = bolt_obj_2_feature_vector(test_data, feature_name_list)

    # Do for all data for clustering purposes
    all_feature_vector, all_adjective_dictionary = bolt_obj_2_feature_vector(all_data, feature_name_list)
   
    print("Created feature vector containing %s" % feature_name_list)

    #import pdb; pdb.set_trace()
    # Run k-means
    # k_means_labels, k_means_cluster_centers, clusters_idx = run_kmeans(all_feature_vector['thermal_hold'], 3, all_data['thermal_hold'])
   
    # Run KNN

    #motion_name = 'squeeze'
    #adjective_name = 'bumpy'

    knn_score, knn_predict, knn_comparison = train_knn(train_feature_vector[motion_name], train_adjective_dictionary[adjective_name], test_feature_vector[motion_name], test_adjective_dictionary[adjective_name], 5)
        
    all_knn_results[adjective_name][motion_name]

    # Give true and false results
    TP, TN, FP, FN = true_false_results(knn_predict, test_adjective_dictionary[adjective_name])

    # Give Mattews Correlation Coefficient
    MCC = mattews_corr_coef(TP,TN,FP,FN)

    import pdb; pdb.set_trace()
    print "Ran KNN"
    

# Parse the command line arguments
def parse_arguments():
    """Parses the arguments provided at command line.
    
    Returns:
    (input_file, adjective_file, range)
    """
    parser = OptionParser()
    parser.add_option("-i", "--input_file", action="store", type="string", dest = "in_h5_file")
    parser.add_option("-o", "--output", action="store", type="string", dest = "out_file", default = None) 
    parser.add_option("-a", "--input_adjective", action="store", type="string", dest = "in_adjective_file")

    (options, args) = parser.parse_args()
    input_file = options.in_h5_file #this is required
   
    if options.out_file is None:
        (_, name) = os.path.split(input_file)
        name = name.split(".")[0]
        out_file = name + ".pkl"
    else:    
        out_file = options.out_file
        if len(out_file.split(".")) == 1:
            out_file = out_file + ".pkl"
    
    adjective_file = options.in_adjective_file

    return input_file, out_file, adjective_file


if __name__ == "__main__":
    input_file, out_file, adjective_file = parse_arguments()
    main(input_file, adjective_file)
