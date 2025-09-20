# Dissannounce

ITMO PhD dissertaion aggregator

## Set up prerequisites

```sh
create -n dissannounce python=3.13
pip install beautifulsoup4==4.13.5 click==8.3.0 pandas==2.3.2 requests==2.32.5 tqdm==4.67.1
```

## Pull data

**Manually** get list of dissertations by scrolling down on [this page](https://dissovet.itmo.ru/index.php?main=108). Then update the list of identifiers [here](assets/numbers.txt). Then download the web pages:

```sh
python -m dne pull
```

## Gather statistics

Generate the [dataframe](assets/stats.tsv) using the collection of `html` files from the last step:

```sh
python -m dne stats
```

## Aggregate gathered data

Use `list` command to aggregate data by required column:

```sh
python -m dne list speciality -n 15
```

Example of the command output:

```sh
   speciality  count  percentile
1       1.3.6     68   12.078153
2    01.04.05     34   18.117229
3    05.13.17     30   23.445826
4    05.11.07     25   27.886323
5       2.3.1     24   32.149201
6       1.3.8     23   36.234458
7       4.3.3     20   39.786856
8    05.04.03     19   43.161634
9       2.2.6     19   46.536412
10      2.7.1     17   49.555950
11      1.2.1     17   52.575488
12   05.18.07     17   55.595027
13      2.3.8     13   57.904085
14      2.4.8     13   60.213144
15      2.3.6     12   62.344583
```
