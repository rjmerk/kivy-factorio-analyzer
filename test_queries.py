import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from sql import Base, recipe_inputs_with_ratios, Recipe, RecipeInput, Component


@pytest.fixture
def session():
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


@pytest.mark.parametrize(
    "time_output,output_amount,needed_input,time_input,input_amount, expected",
    [(0.5, 1, 3, 0.5, 2, 1.5),  # copper wire -> electronic circuit
     (6, 1, 1, 0.5, 1, 1/12),  # inserter -> green science
     (0.5, 1, 5, 3.2, 1, 32),   # stone brick -> wall
    ])
def test_ratios(session, time_output, output_amount, needed_input,
                time_input, input_amount, expected):
    component_out = Component(name="a")
    component_in = Component(name="b")
    recipe = Recipe(
        time=time_output,
        output=component_out,
        output_amount=output_amount,
        produced_by="")
    recipe_input = RecipeInput(
        recipe=recipe,
        component=component_in,
        amount=needed_input
    )
    recipe_for_input = Recipe(
        time=time_input,
        output=component_in,
        output_amount=input_amount,
        produced_by=""
    )
    session.add(component_out)
    session.add(component_in)
    session.add(recipe)
    session.add(recipe_input)
    session.add(recipe_for_input)
    session.commit()
    result = recipe_inputs_with_ratios(session).first()
    assert result.ratio == pytest.approx(expected)
