#from nltk.corpus import wordnet as wn

from firebase import firebase

firebase = firebase.FirebaseApplication("https://trackx-94915.firebaseio.com/")
#result = firebase.get("/user", "1854520056")
new_value = firebase.put("/user", "18577536691", {"Balance": 60})
#print result['Balance']
result2 = firebase.get("/user", "1854520056")
print result2['Balance']
'''
blob = TextBlob("spent $50 on milk")

for np in blob.noun_phrases:
    print np


drinks = wn.synset('beverage.n.01')
foods = wn.synset('food.n.01')

foods = list(set([w for s in food.closure(lambda s:s.hyponyms()) for w in s.lemma_names()]))

print foods
if 'milk' in foods:
    print "Present"
'''
