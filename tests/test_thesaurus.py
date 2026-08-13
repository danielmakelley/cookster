from ranking import rank_recipes


def test_aubergine_matches_eggplant():
    candidates = [
        {'id': 1, 'title': 'Roasted Eggplant', 'ingredients': 'eggplant, olive oil, salt', 'steps': 'Roast eggplant until tender.'},
        {'id': 2, 'title': 'Mashed Potato', 'ingredients': 'potatoes, butter, milk', 'steps': 'Boil and mash.'}
    ]

    results = rank_recipes(candidates, 'aubergine', top_n=2)
    # top result should be the eggplant recipe because 'aubergine' maps to 'eggplant'
    assert results[0]['id'] == 1
