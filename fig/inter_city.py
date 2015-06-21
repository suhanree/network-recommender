# coding: utf-8
get_ipython().magic(u'history')
get_ipython().magic(u'paste')
if os.path.exists(graph_pickle_filename):
        with open(graph_pickle_filename, 'r') as f:
                (gg, city_prop) = pickle.load(f)
            print "Read the graph info from pickled file."
        else:
                (gg, city_prop) = read_file(network_filename, user_by_city_filename)
                with open(graph_pickle_filename, 'wb') as f:
                        pickle.dump((gg, city_prop), f)
            
if os.path.exists(pos_pickle_filename):
        with open(pos_pickle_filename, 'r') as f:
                pos = pickle.load(f)
            print "Read the position info from pickled file."
        else:
                pos = sfdp_layout(gg, groups=city)
                with open(pos_pickle_filename, 'wb') as f:
                        pickle.dump(pos, f)
                    print "Done calculating positions."
            
with open(graph_pickle_filename, 'r') as f:
        (gg, city_prop) = pickle.load(f)
    
with open(pos_pickle_filename, 'r') as f:
        pos = pickle.load(f)
    
pos
for v in gg.vertices():
    s += str(pos[v][0]) + , , + str(pos[v][1]) + '\n'
    
for v in gg.vertices():
    s += str(pos[v][0]) + ' ' + str(pos[v][1]) + '\n'
    
s= ;'
s = ''
for v in gg.vertices():
    s += str(pos[v][0]) + ' ' + str(pos[v][1]) + '\n'
    
len(S)
len(s)
s[:100]
s = ''
for v in gg.vertices():
    s += str(pos[v][0]) + ' ' + str(pos[v][1]) + ' ' + str(city_prop[v]) + '\n'
    
s[:100]
with open('position_city', 'w') as f:
    write(s,f)
    
with open('position_city', 'w') as f:
    f.write(s)
    
gg
for e in gg.edges()
inter_city_edges = {}
for e in gg.edges():
    source = e.source()
    target = e.target()
    source_city = city_prop[e.vertex(source)]
    target_city = city_prop[e.vertex(target)]
    if source_city != target_city:
        if source < target:
            if (source, target) not in inter_city_edges:
                inter_city_edges[(source, target)] = 1
            else:
                inter_city_edges[(source, target)] += 1
        else:
            if (target, source) not in inter_city_edges:
                inter_city_edges[(target, source)] = 1
            else:
                inter_city_edges[(target, source)] += 1
                
for e in gg.edges():
    source = gg.vertex_index(e.source())
    target = gg.vertex_index(e.target())
    source_city = city_prop[e.source()]
    target_city = city_prop[e.target()]
    if source_city != target_city:
        if source < target:
            if (source, target) not in inter_city_edges:
                inter_city_edges[(source, target)] = 1
            else:
                inter_city_edges[(source, target)] += 1
        else:
            if (target, source) not in inter_city_edges:
                inter_city_edges[(target, source)] = 1
            else:
                inter_city_edges[(target, source)] += 1
                
gg.edges()[0]
i = gg.edges()
i.next()
e = i.next()
e
e.source
e.source()
e.source().index
e.source().index()
e.source().get_index()
e.source()
v= e.source()
v.out_degree
v.out_degree()
v.out_degree()
for e in gg.edges():
    source = int(e.source())
    target = int(e.target())
    source_city = city_prop[e.source()]
    target_city = city_prop[e.target()]
    if source_city != target_city:
        if source < target:
            if (source, target) not in inter_city_edges:
                inter_city_edges[(source, target)] = 1
            else:
                inter_city_edges[(source, target)] += 1
        else:
            if (target, source) not in inter_city_edges:
                inter_city_edges[(target, source)] = 1
            else:
                inter_city_edges[(target, source)] += 1
                
inter_city_edges.values
inter_city_edges.values()
inter_city_edges.keys()
for e in gg.edges():
    source = int(e.source())
    target = int(e.target())
    source_city = city_prop[e.source()]
    target_city = city_prop[e.target()]
    if source_city != target_city:
        if source < target:
            if (source_city, target_city) not in inter_city_edges:
                inter_city_edges[(source_city, target_city)] = 1
            else:
                inter_city_edges[(source_city, target_city)] += 1
        else:
            if (target_city, source_city) not in inter_city_edges:
                inter_city_edges[(target_city, source_city)] = 1
            else:
                inter_city_edges[(target_city, source_city)] += 1
                
inter_city_edges.keys()
inter_city_edges = {}
for e in gg.edges():
    source = int(e.source())
    target = int(e.target())
    source_city = city_prop[e.source()]
    target_city = city_prop[e.target()]
    if source_city != target_city:
        if source < target:
            if (source_city, target_city) not in inter_city_edges:
                inter_city_edges[(source_city, target_city)] = 1
            else:
                inter_city_edges[(source_city, target_city)] += 1
        else:
            if (target_city, source_city) not in inter_city_edges:
                inter_city_edges[(target_city, source_city)] = 1
            else:
                inter_city_edges[(target_city, source_city)] += 1
                
inter_city_edges.keys()
len(inter_city_edges.keys())
len(inter_city_edges.values())
sum(inter_city_edges.values())
gg
for e in gg.edges():
    source = int(e.source())
    target = int(e.target())
    source_city = city_prop[e.source()]
    target_city = city_prop[e.target()]
    if source_city != target_city:
        if source.city < target.city:
            if (source_city, target_city) not in inter_city_edges:
                inter_city_edges[(source_city, target_city)] = 1
            else:
                inter_city_edges[(source_city, target_city)] += 1
        else:
            if (target_city, source_city) not in inter_city_edges:
                inter_city_edges[(target_city, source_city)] = 1
            else:
                inter_city_edges[(target_city, source_city)] += 1
                
for e in gg.edges():
    source = int(e.source())
    target = int(e.target())
    source_city = city_prop[e.source()]
    target_city = city_prop[e.target()]
    if source_city != target_city:
        if source_city < target_city:
            if (source_city, target_city) not in inter_city_edges:
                inter_city_edges[(source_city, target_city)] = 1
            else:
                inter_city_edges[(source_city, target_city)] += 1
        else:
            if (target_city, source_city) not in inter_city_edges:
                inter_city_edges[(target_city, source_city)] = 1
            else:
                inter_city_edges[(target_city, source_city)] += 1
                
inter_city_edges.keys()
len(inter_city_edges.keys())
inter_city_edges = {}
for e in gg.edges():
    source = int(e.source())
    target = int(e.target())
    source_city = city_prop[e.source()]
    target_city = city_prop[e.target()]
    if source_city != target_city:
        if source_city < target_city:
            if (source_city, target_city) not in inter_city_edges:
                inter_city_edges[(source_city, target_city)] = 1
            else:
                inter_city_edges[(source_city, target_city)] += 1
        else:
            if (target_city, source_city) not in inter_city_edges:
                inter_city_edges[(target_city, source_city)] = 1
            else:
                inter_city_edges[(target_city, source_city)] += 1
                
len(inter_city_edges.keys())
get_ipython().system(u'ls -F --color ')
sum(inter_city_edges.values())
with open('../fig/intercity_edges', 'w') as f:
    for a in inter_city_edges:
        f.write(str(a[0])+' '+str(a[1]) + ' ' + str(inter_city_edges[a]) + '\n')
        
get_ipython().system(u'ls -F --color ')
get_ipython().magic(u'pwd ')
with open('../intercity_edges', 'w') as f:
    for a in inter_city_edges:
        f.write(str(a[0])+' '+str(a[1]) + ' ' + str(inter_city_edges[a]) + '\n')
        
