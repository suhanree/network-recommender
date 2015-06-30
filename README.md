# Exploring Recommenders with Networks

## Introduction
With the big growth in online commerce in recent years, 
recommendation systems (recommenders) have become very popular.
Recommenders try to match certain *items* to specific *users*, based on
existing information, and usually show recommended items to users
in their web interfaces.

If user attributes and item attributes exist, those information 
can be arranged in a shared space,
so that user-item *distances* can be used to find out how well they match
(content-based methods).

If ratings, given by users for
items, exist (usually, in values of 1 to 5),
recommenders try to predict unknown ratings using past ratings.
One simple method is to use average ratings for predictions
(biases of users and/or items can be considered, in addition).
But that might not be good enough, because we know that users are not the
same; rather we users are quite diverse with many unique characteristics.
Then one thing we can do is using the user attributes for grouping
users, and then use members of the same group
for predictings (demographic filtering).

We can compare users (or items) by looking at 
similarities between their past ratings to find out similar users (or
items) for predictions.
Or, we can find latent factors using matrix factorization techniques
(collaborative filtering) [1,2].

This type of filtering methods will give us better predictions compared to 
models using averages,
because we are now considering diverse characteristics of users.
Each method mentioned above has its own drawbacks,
which we will not go into detail here,
and most recommendation systems combine some existing methods to find better
predictions (hybrid models).

Another recent big trend is the growth and availability of huge social networks that
have the information of how users are connected with each other.
Then one can ask a question: if we use social networks in recommenders in
addition to methods described above, will the performance of recommenders be enhanced?
We already know the answer. The answer is yes; because we tend to become
friends with similar people, or we become similar with friedns by interacting
with them, and sharing information with them [3-5].

Then the next question is: how do we incorporate network information into
recommenders?
Here I implement
and analyze the simplest approach of using past ratings of friends for
predictions.
(we may call it *network filtering*, or NF, for convenience).
<!--- 
{% include figure.html src="fig/net_rec2.png" caption="Fig.1. Schmatic diagram
    describing the model" %}
--->
![Fig.1](fig/net_rec1.png "Fig.1. Schematic diagram describing the model")
The above figure describes the method. If a user, named Suhan, has two friends, Jef
and Vik, who rated a business, named Ovo Cafe, we assume that Suhan's rating is
more likely to be closer to their ratings than the average rating.
To test this simple model, we will use the data from [Yelp Dataset
Challenge](http://www.yelp.com/dataset_challenge).

## Data

The data consist of five json files, and each file has information on
users, businesses, reviews (with ratings), tips, and check-ins.
The data is composed by Yelp to represent 10 cities: 
Phoenix, Las Vegas, Charlotte, Montreal, Edinburgh, Pittsburgh,
Madison, Karlsruhe, Urbana-Champaign, and Waterloo (ordered by the number of
businesses).
Even though there was no need for data cleaning, some preprocessing
had to be performed (see Appendix for technical details).
If I briefly describe the preprocessing:

1. We only need users, bussinesses, and ratings (from the file of reviews).
    We'd like to do some city-by-city analysis, so we will separate data
    into 10 subsets, one for each city.
2. First, each businsess was assigned a city by their location information. Due to the
   nature of the dataset, every business was classified cleanly.
3. Second, by going through every rating with (user, business) information, we
   were able to assign users to each city. One problem arises when
   there are users who left ratings on multiple cities (about 5% of users).
   In those cases, we looked at friends of these users, and found cities where
   the majority of friends reside. If there is no majority or there is not enough
    friends to determine, a city was assigned randomly.
4. Since we are only concerned with users who are in social network (with
   friends), we dropped users without any friend and their ratings from the
    dataset. The number of users is reduced from 366,715 to 174,094 here.
5. If we ignore network edges between users in different cities (about 22% of
   edges are dropped here), we now have 10 separate subsets of network data.
    Finally, here
    we further drop users by only keeping the biggest component of the
    network for each city. The number of users now has become 147,114.
    For example, the network (the biggest component) of Montreal with 3,071
    users and 9,121 edges looks like below (using sfdp layout in graph_tool
    library [6]). 
![Fig.2](fig/network3b_sfdp.png "Fig.2. Network for the city of Montreal")

Now we will briefly examine the city-by-city data (for more detailed analysis, 
look at
[EDA.ipynb](https://github.com/suhanree/network-recommender/blob/master/code/EDA.ipynb),
done in ipython notebook format).
If we compare cities by counts, the figure below shows ratios for
numbers of users, businesses, and ratings (before we drop users based on
the structure of social network).
There are two big cities, Phoenix and Las Vegas, and five medium cities, and
three small cities.
![Fig.3](fig/ratios_by_city.png "Fig.3. Ratios of counts by city")
One thing that catches our eyes is that the number of users are the highest for
Las Vegas, even though the number of businesses is not the highest.
The numbers of users per business for each city and average degrees are as below.

||Phoenix|Las Vegas|Charlotte|Montreal|Edinburgh|Pittsburgh|Madison|Karlsruhe|Urbana-Champaign|Waterloo|
|---|---|---|---|---|---|---|---|---|---|---|
|users per business|5.09|11.03|4.79|3.54|1.07|5.85|5.07|0.81|6.25|3.18|
|average degree|8.6|17.2|6.0|5.4|9.4|5.2|4.6|2.4|2.7|2.3|

It also appears that the average degree for Las Vegas (around 17) is more
than twice as much as average degrees for other cities.
Having more tourists alone cannot explain this phenomenon, and I can only
conclude that there are just more active users in Las Vegas, based on this
data. There may exist other outside factors I am not aware of.

Another interesting thing is that distributions of ratings are different for
some cities. Overall ratings are skewed toward 5 with the mean at 3.75.
But if we look at ratings distributions city by city, we can see a clear difference.
![Fig.4](fig/ratings_dist.png "Fig.4. Ratings distributions")
In Phoenix and Las Vegas, 5 is given the most, but in Charlotte and Montreal, 4
is the most given rating. People in big cities are more generous? Maybe.

Now we turn our attention to the main focus of this project: a recommender with 
a social network.

## Model

### How we compare models
Models will be compared using the average RMSE (Root Mean Squared Error)
from the K-fold cross-validation (K=10).
First, train and test sets
are chosen randomly out of all given ratings, and next, the train set is
divided into K folds randomly again.
Then, each fold is used as a validation set to find an RMSE,
and the averaged RMSE is obtained for the given model.

### Model implemented
The network model implemented here is the simplest one:
predicting ratings based on past ratings done by friends.
(A similar model based on the same idea has been already studied thoroughly
 in Ref.3.)
It makes sense because of the homophily. Also friends tend to spend time together,
so they are more likely to visit/use the same businesses and to get influenced 
with each other.
If that is true, predictions based on ratings by friends will be more accurate
on average.
The figure below seems to show that our assumption might be true.
![Fig.5](fig/friends.png "Fig.5. How predictions given by the number of ratings by friends change RMSE")
For the city of Montreal, if we use the business average as the prediction, the
RMSE is 1.065, and this value is a good baseline to compare to.
Now we look at predictions with the certain numbers of friend ratings, and find
RMSE's for these subsets of data as we increase this number.
And do the same with only friends of friends (excluding friends).
As expected, as this number increases, RMSE's tend to go down, and
friends of friends tend to give less accurate predictions.

Because the accuracy is not as good
if there is only one friend rating, 
our model has the lower limit (also the upper limit, which is not as important) for
the number of friend ratings to consider.
If the number of friend ratings is less than the lower limit, there will
be no prediction; while if it exceeds the upper limit, the model will
choose friend ratings randomly for predictions.
The figure below shows how RMSE changes as this lower limit
increases for Montreal data. 
Also the *coverage*, the term used in Ref.3 to express the ratio of
ratings that were predicted, decreases, too.
![Fig.6](fig/limit.png "Fig.6. How RMSE changes with the limit for friend
        ratings")
The coverage is around 0.2 at the lower limit at 2, but it decreases
significantly as the limit increases.
Other cities show almost the same behavior (not shown here).
Due to this property, we set the lower limit at 2, and the model has to be
combined with other models to get predictions for all possible cases.

## Results

Now we compare our network model (NF) with other models.
We consider four models: (1) model that uses business average ratings (baseline
model); (2) model using collaborative filtering with matrix factorization,
also using business biases (CF);
(3) model with friend ratings, where the business average ratings are
used when the method is not applicable (NF + average); (4) model with 
friend ratings, where only subsets satisfying our condition are considered.
The figure below shows RMSE's for 7 cities (other 3 cities are too small
to show any meaningful results).
![Fig.7](fig/rmse.png "Fig.7. RMSE's for different models")

The baseline RMSE for each city were obtained by predicting
the average rating for each business.
There are some discrepancies between cities.
It is very low for Edinburgh, but it is too small to have any significant meaning.
Charlotte and Montreal showed relatively low baseline RMSE's, which may be related to
the ratings distribution we observed earlier (ratings were centered aroung 4,
while ratings for other big cities were different).

For CF, the grid search was performed to find the right parameter set.
The parameters are n_features (number of latent features), learning_rate
(learning rate for the stochastic gradient descent), and
regularization_parameter (regularization parameter).
A parameter that seems to give the best RMSE was (n_features=2,
learning_rate=0.011, regularization_parameter=0.12).
This CF model has features that can add user- or item-biases.
Item-biases made RMSE's lower, while user-biases didn't.
So only item-biases were considered when computing RMSE's.
Somehow CF didn't give us significantly better RMSE's compared to the baseline
model. For Montreal, CF was a little worse than the baseline model.

For the network model (NF), RMSE's for subsets are significantly lower for all cities 
when we only consider predictions done by this method ignoring cases without
prediction (they are not comparable because RMSE's are not from the same set of
data).
But if we combine two models, NF and average, we can compare RMSE's with
other models. RMSE's are not significantly lower as subset RMSE's are, but 
RMSE's are lower than those from CF in all cities shown.


## Discussions

* The question I asked can be answered; now we observed that 
networks can help improve recommenders.

* In most cases, hybrid models are needed,
  because social networks cannot be applied to every
  case as shown above. 

* This is a well-known problem, and I believe
many computer scientists and data scientists have been tackling this problem
in academia and industry for sevaral years now [3-5,7,8]. 

* Other approaches incorporating networks are possible. One model I planned to
  do, but couldn't due to the time constraint, 
  was using communities of the given network.

* There are many possible applications for this model.

## References

1. Mining of Massive Datasets, by Jure Leskovec, Anand Rajaraman, and Jeffrey D. Ullman,
    [http://infolab.stanford.edu/~ullman/mmds/book.pdf](http://infolab.stanford.edu/~ullman/mmds/book.pdf) (2014). 

1. Recommender Systems: Types of Filtering Techniques, by I. Ryngksai and L.
   Chameikho, International Journal of Engineering Research & Technology, Vol.
   3, Issue 11 (2014).

1. A social network-based recommender system, by Wesley W. Chu and Jianming He,
   Doctoral Dissertation, published by University of California at Los Angeles (2010).

1. Use of social network information to enhance collaborative filtering performance,
    by Fengkun Liu and Hong Joo Lee, Expert Systems with Applications, 37,
    4772-8 (2010).

1. Social   Recommender Systems: An Influence on Public Media,
    by Bornali Borah, Priyanka Konwar, and Gypsy Nandi,
    I3CS15 (Internaional Conference on Computing and Communication Systems)
            (2015).

1. “The graph-tool python library”, by Tiago P. Peixoto, 
   [figshare](http://figshare.com/articles/graph_tool/1164194). DOI:
   10.6084/m9.figshare.1164194 (2014).

1. Systems and methods to facilitate searches based on social graphs and affinity groups,
  by David Yoo, US Patent App. 14/516,875, 
  [https://www.google.com/patents/US20150120589](https://www.google.com/patents/US20150120589),
  (2015).

1. The Cutting Edge: Network Analytics for Financial Fraud Detection and
   Mitigation, by Scott Mongeau,
   [http://sctr7.com/2014/06/27/the-cutting-edge-network-analytics-for-financial-fraud-detection-and-mitigation/]
   (http://sctr7.com/2014/06/27/the-cutting-edge-network-analytics-for-financial-fraud-detection-and-mitigation/)
   (2014).

1. I thank mentors and instructors who helped finish this project: Tammy,
   Robert, Karthik, Dominique, and Tom.

## Appendix: technical details.
Here I present some technical details for this project. First, a diagram
representing data flow is given below.
![Fig.8](fig/data_flow.png "Fig.8. Data flow diagram")
The original data are given by three json files at the top (not stored in this
repo due to the sizes), and three python codes (`extend_network.py`,
`make_dataframes.py`, and `find_users_by_city.py`) process these files to produce
separate network files and ratings information, one for each city.
During the process, intermediate results of pandas dataframes and ID mapping
information are stored in pickled files for future usages.

After preprocessing, models can be run. I have implemented two methods.
One for the
collaborative filtering (CF; `factorization.py`), implemented using SVD with
stochastic gradient descent.
The other for the friend-based network model (NF; `using_friends.py`),
implemented using python for this project.
In addition, Validator class (`validator.py`) was implemented to read input
files, and perform K-fold cross-validation.

To run the models (CF and NF), two codes are used: `run_cf.py` and `run_nf.py`,
respectively. Model parameters can be given to the model using a text file.

For example, for the CF model,
if you have a file, called `input_params_cf`, with 4
lines like this,
```
0 1 2 3 4 5 6 7 8 9
2
0.011
0.12
```
and if you run the code as below,
```sh
$ run_cf.py input_params_cf 0 1
```
it will run the CF model for all cities (0~9) with `n_features=2`,
   `learning_rate=0.011`, and `regularization_param=0.12`. 
In the command line, 0 and 1 means it will not include user bias (0) and 
that it will consider item biases (1).

To run the NF model, we also need a file, called `input_params_nf`,
with 3 lines like this,
```
0 1 2 3 4 5 6 7 8 9
2
20
```
and run the code as below.
```sh
$ run_nf.py input_params_nf 1
```
Then, it will run the NF model for all cities (0~9) with the lower and upper
limits of the number of ratings by friends as 2 and 20.
In the command line, 1 means it will use the business average rating
if there is not enough ratings by friends. If this value is 0, it will
predict only when ratings by friends are available, 
and find an RMSE based on only those cases.
