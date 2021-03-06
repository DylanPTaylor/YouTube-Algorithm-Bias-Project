
"""
Author: Dylan Taylor
UCID: 30078900
Date: 09/12/2021 

This file holds all the general purpose methods used throughout the project
Its not beautiful code, but it works.

This is were most of the technical stuff happens
"""

def Home():
    return "SET ME TO WHERE EVER YOU ARE STORING ALL THE NETWORK DATA"

import json
from Youtube import fetch_data, get_genres
import random
import os
import networkx as nx
from datetime import datetime
import shutil



HOME = Home()


def Log(message):
    with open(HOME+"\\log.txt", 'a') as log:
        log.write("\n---Date Time: " +
                  datetime.now().strftime("%d/%m/%Y %H:%M:%S")+' ---')
        log.write("Message: "+message+'\n')
        log.close()

def load_genres_from_file():
    genres = []
    with open(HOME+"\\VideoData\\genres.json") as in_file:
        genre_list = json.load(in_file)
        for dict in genre_list:
            genres.append(dict["title"])
    
    return genres

# region Graph Functions

"""
Driver method
"""
def graph_data(crawler):
    var = populate_crawler(crawler)
    if var == 0:
        return 0
    update_node(crawler)

"""
Takes in a graph where the nodes have a "probabilites" attribute.

The probabilites attribute is generated by summing the distribution of genres of suggested videos 
seen at each visit to a particular node/video. The number of times we see a video is equal
to the the nodes in degree, by definition of an edge. (Except for the starting node).
So we divide the summed distribution by the in-degree to get the average distribution for that one video.
Does not return anything as it works in place.
"""
def compute_averages(graph):
    for Id in graph.nodes():
        node = graph.nodes()[Id]
        probabilities = node["probabilities"]

        in_degree = graph.in_degree(Id)

        sum = 0
        for prob in probabilities:
            sum += float(probabilities[prob])

        if in_degree == 0: in_degree+=1

        try:
            if sum/in_degree > 1.1:
                    in_degree += 1 # fixes starting nodes
            for probability in probabilities:
                average = float(probabilities[probability]) / in_degree
                probabilities[probability] = average
            graph.nodes()[Id]["probablities"] = probabilities
        except Exception:
            continue

"""
Does the same as above, but sum the probabilities for each video from each crawler network
and divide by the number of times that video was visited by different crawlers.

This assumes the above function has been run on every crawler network
"""
def compute_final_averages(graph):
    for Id in graph.nodes():
        node = graph.nodes()[Id]
        probabilities = node["probabilities"]

        duplication = node["duplication"]

        try:
            for probability in probabilities:
                average = float(probabilities[probability]) / duplication
                probabilities[probability] = average
            graph.nodes()[Id]["probablities"] = probabilities
        except Exception:
            continue

"""
add the genre distribution for this visit to this videos distribution
"""
def update_node(crawler):
    probabilities = {}

    genreProbability = 1 / len(crawler.candidateVideos)

    # Get the probability of choosing each genre from these candidates
    for candidate in crawler.candidateVideos:
        candidateGenre = crawler.candidateGenres[candidate]
        try:
            probabilities[candidateGenre] += genreProbability
        except KeyError:
            probabilities[candidateGenre] = genreProbability

    # Add those probabilities to this nodes probability array
    for genre in probabilities:
        try:
            crawler.probabilities[genre] += probabilities[genre]
        except KeyError:
            crawler.probabilities[genre] = probabilities[genre]

    node = crawler.graph.nodes()[crawler.video]
    node["probabilities"] = crawler.probabilities

"""
add toAdd distribution to initial distribution
"""
def add_probabilities(initial, toAdd):
    if type(initial) != dict:
        initial = json.loads(initial.strip().replace("\'", "\""))
    if type(toAdd) != dict:
        toAdd = json.loads(toAdd.strip().replace("\'", "\""))
    for genre in toAdd:
        try:
            initial[genre] += toAdd[genre]
        except KeyError:
            initial[genre] = toAdd[genre]
    return initial

#region Network File Writing

"""
This entire region was written at the start of the semester
before I got too deep into NetworkX. They all helped to save a network to csv files
"""
def write_nodes(nodes, path):
    with open(path, 'w+') as file:
        file.write("Id;Genre;Probabilities\n")
        for id in nodes:
            node = nodes[id]
            file.write(
                id + ";"+str(node["genre"])+"; "+str(node["probabilities"])+"\n")


def write_edges(adjLists, path):
    with open(path, 'w+') as file:
        file.write("Source,Target,weight\n")
        for thisNode in adjLists:
            for neighbour in adjLists[thisNode]:
                try:
                    file.write(
                        thisNode+','+neighbour+',' + str(adjLists[thisNode][neighbour]['weight']) + '\n')
                except:
                    file.write(
                        thisNode+','+neighbour + '\n')

def load_edges(graph,path):
    edges_path = path+"edges.csv"
    with open(edges_path) as edges_file:
        edge = edges_file.readline()  # header
        edge = edges_file.readline()  # first edge
        while (edge != ""):
            edge = edge.split(",")
            graph.add_edge(edge[0], edge[1], weight=int(edge[2]))
            edge = edges_file.readline()
            

def load_edges_inverse_weight(graph,path):
    edges_path = path+"edges.csv"
    with open(edges_path) as edges_file:
        edge = edges_file.readline()  # header
        edge = edges_file.readline()  # first edge
        while (edge != ""):
            edge = edge.split(",")
            graph.add_edge(edge[0], edge[1], weight=(1/int(edge[2])))
            edge = edges_file.readline()

def load_edges_no_weight(graph,path):
    edges_path = path+"edges.csv"
    with open(edges_path) as edges_file:
        edge = edges_file.readline()  # header
        edge = edges_file.readline()  # first edge
        while (edge != ""):
            edge = edge.split(",")
            graph.add_edge(edge[0], edge[1])
            edge = edges_file.readline()
                    
def load_nodes(graph, path):
    nodes_path = path + "nodes.csv"
    with open(nodes_path) as node_file:
        node = node_file.readline()  # header
        node = node_file.readline()  # first node
        while (node != ""):
            node = node.split(';')
            node[2] = node[2].strip()

            graph.add_node(node[0], genre=node[1], probabilities=json.loads(
                node[2].replace("\'", "\"")))
            node = node_file.readline()

def load_graph(path, inverse = False, weighted = True):
    graph = nx.DiGraph()

    load_nodes(graph, path)
    if inverse:
        load_edges_inverse_weight(graph,path)
    elif not weighted:
        load_edges_no_weight(graph,path)
    else:
        load_edges(graph, path)
    
    return graph
    
def write_graph(graph, path):
    if not os.path.exists(path):
        os.makedirs(path)
    write_edges(dict(graph.adj), path+"edges.csv")
    write_nodes(graph.nodes(), path+"nodes.csv")

#endregion

"""
Takes a source directory and a target directory.
This takes all the networks in the source directory and compiles them into a single
network and places that into the target directory.
"""
def compile_networks(source, target):
    final_graph = nx.DiGraph()

    #We name the graph based on the date
    final_graph_path = target+datetime.now().strftime("%d-%m-%Y")

    #for overwriting purposes
    if os.path.exists(final_graph_path):
        shutil.rmtree(final_graph_path)

    os.makedirs(final_graph_path)

    #for each graph we need to compile
    for graph in os.listdir(source):

        #load the nodes
        nodes = open(source+graph+"\\nodes.csv", 'r')
        nodes.readline()
        node = nodes.readline()
        while (node != ""): #for each line in the file
            
            #extract node info
            node = node.replace("\n", "").split(';')

            # If this node is already in this graph, add this duplicated nodes probabilities to it,
            # will take average later using the duplication field
            if final_graph.has_node(node[0]):
                nodeInGraph = final_graph.nodes()[node[0]]  #get it from the graph
                nodeInGraph["probabilities"] = add_probabilities(
                    nodeInGraph["probabilities"], node[2])  #add probabilities together
                nodeInGraph["duplication"] = int(
                    nodeInGraph["duplication"]) + 1 #Increment so we can find average later
            # other wise add it with this nodes probabilities.
            else:
                final_graph.add_node(
                    node[0], genre=node[1], probabilities=node[2], duplication=1)

            node = nodes.readline()

        #Same thing as nodes, but now edges
        edges = open(source+graph+"\\edges.csv", 'r')
        edges.readline()
        edge = edges.readline()
        while (edge != ''):
            edge = edge.split(',')

            edge_weight = final_graph.get_edge_data(
                edge[0], edge[1], default=0)
            #If this edge doesnt exist
            if edge_weight == 0:
                #Add this edge with this graph weight for this edge
                final_graph.add_edge(edge[0], edge[1], weight=int(edge[2]))
            else:
                #Sum the edge weights
                final_graph[edge[0]][edge[1]]["weight"] = int(
                    edge_weight["weight"])+int(edge[2])

            edge = edges.readline()

    #Take average of probablity distributions
    compute_final_averages(final_graph)
    #save me
    write_graph(final_graph, final_graph_path+"\\")
# endregion

# region Crawler Functions

#Select numberToPick videos from videos
def select_random(videos, numberToPick):
    random_videos = []
    for i in range(numberToPick):
        #roll the dice
        my_random_int = random.randint(0, len(videos)-1) #len(videos) decreases with every loooooooo0000ooooo0000op
        
        #take that video
        selected_video= videos[my_random_int]

        #remove it so we dont pick it again
        videos.remove(selected_video)
        
        #append to return it
        random_videos.append(selected_video)
    return random_videos


def populate_crawler(crawler):
    
    #Get the Json for this video
    json_data = fetch_data(crawler.video)

    if json_data == 0: #we threw an error
        return 0

    #get the suggested videos
    crawler.candidateVideos = json_data["candidate videos"][:
                                                            crawler.numberOfCandidatesToConsider]
    #get this videos genre
    crawler.genre = json_data["genre"]
    
    #use the Youtube Data V3 API to get suggested video genres
    crawler.candidateGenres = get_genres(crawler.candidateVideos)
    
    #If we have visited this video with this crawler
    if crawler.graph.has_node(crawler.video):
        #get the node
        node = crawler.graph.nodes()[crawler.video]
        #set the crawlers probs to this videos probs -> needed for update_node -> see driver method at start of file
        crawler.probabilities = node["probabilities"]
    else:
        crawler.graph.add_node(
            crawler.video, genre=crawler.genre, probabilities={})
        crawler.probabilities = {}

    json_data = None
    return 1


def add_self(crawler):
    crawler.graph.add_node(crawler.video, genre=crawler.genre,
                           probabilities=crawler.probabilities)
# endregion
