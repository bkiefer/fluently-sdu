# Using the Official Docker Container

## Train NLU with all data from the `data` direcory
Defaults: training files are in `data`, config (pipeline def) in `config.yml`

`./rasadock train --num-threads=32`

## Shuffle and split data: results in `train_test_split`
`./rasadock data split nlu`

## Train NLU with the train split of the data
`./rasadock train nlu --num-threads=16 --nlu train_test_split/training_data.yml`

## Test performance on test split of data
`./rasadock test nlu --nlu train_test_split/test_data.yml`

## Larger cross-validation test
`./rasadock test nlu --nlu data/nlu --cross-validation --folds 5`

## Comparing different pipeline configurations
`./rasadock test nlu --nlu data/univfaq.yml --config config.yml config2.yml`


# Installation From Scratch
```
conda create -n rasa python=3.10 pip
conda activate rasa
pip install rasa
# depending on pipeline: pip install rasa[spacy/full]
```

If a GPU is available, make sure to install the prerequisites for tensorflow
with GPU first, it will then work out of the box

## Build docker image
docker build -f Dockerfile -t voluprof_rasaserver .

## Shuffle and split data: results in `train_test_split`
`rasa data split nlu`

# Train NLU with all data from the `data` direcory
# defaults: training files are in data, config (pipeline def) in config.yml
`rasa train nlu --num-threads=16 --nlu train_test_split/training_data.yml`

# Test performance
# test on this
`rasa test nlu --nlu train_test_split/test_data.yml`

# Larger cross-validation test
`rasa test nlu --nlu data/nlu --cross-validation --folds 5`

# Comparing different pipeline configurations
`rasa test nlu --nlu data/univfaq.yml --config config.yml config2.yml`
