count_query = {
  "aggs": {
    "unique_count": {
      "cardinality": {
        "field": "layers.zbee_nwk.zbee_nwk_zbee_nwk_src.keyword"
      }
    }
  },
  "size": 0,
  "fields": [
    {
      "field": "layers.frame.frame_frame_time",
      "format": "date_time"
    },
    {
      "field": "timestamp",
      "format": "date_time"
    }
  ],
  "query": {
    "bool": {
      "filter": [
        {
          "match_phrase": {
            "packetzapper.request.sniffer": "whsniff"
          }
        },
        {
          "range": {
            "timestamp": {
              "format": "strict_date_optional_time",
              "gte": "now-10m",
              "lte": "now"
            }
          }
        }
      ],
      "should": [],
      "must_not": []
    }
  }
}


zr_query = {
  "aggs": {
    "0": {
      "percentiles": {
        "field": "layers.zbee_nwk.data.data_data_len",
        "percents": [
          50
        ]
      }
    }
  },
  "size": 0,
  "fields": [
    {
      "field": "layers.frame.frame_frame_time",
      "format": "date_time"
    },
    {
      "field": "timestamp",
      "format": "date_time"
    }
  ],
  "query": {
    "bool": {
      "filter": [
        {
          "match_phrase": {
            "packetzapper.request.sniffer": "whsniff"
          }
        },
        {
          "match_phrase": {
            "layers.zbee_nwk.zbee_nwk_zbee_nwk_dst": "0xfffc"
          }
        },
        {
          "match_phrase": {
            "layers.zbee_nwk.zbee_nwk_zbee_nwk_radius": 1
          }
        },
        {
          "range": {
            "timestamp": {
              "format": "strict_date_optional_time",
              "gte": "now-10m",
              "lte": "now"
            }
          }
        }
      ],
      "should": [],
      "must_not": []
    }
  }
}

zed_query = {
  "aggs": {
    "unique_count": {
      "cardinality": {
        "field": "layers.zbee_nwk.zbee_nwk_zbee_nwk_src.keyword"
      }
    }
  },
  "size": 0,
  "fields": [
    {
      "field": "layers.frame.frame_frame_time",
      "format": "date_time"
    },
    {
      "field": "timestamp",
      "format": "date_time"
    }
  ],
  "query": {
    "bool": {
      "filter": [
        {
          "exists": {
            "field": "layers.wpan.wpan_wpan_src64.keyword"
          }
        },
        {
          "match_phrase": {
            "packetzapper.request.sniffer": "whsniff"
          }
        },
        {
          "range": {
            "timestamp": {
              "format": "strict_date_optional_time",
              "gte": "now-10m",
              "lte": "now"
            }
          }
        }
      ],
      "should": [],
      "must_not": []
    }
  }
}

ZC_query = {
  "query": {
    "bool": {
      "filter": [
        {
          "term": {
            "layers.zbee_nwk.zbee_nwk_zbee_nwk_src.keyword": "0x0000"
          }
        }
      ]
    }
  },
  "aggs": {
    "0-bucket": {
      "filter": {
        "bool": {
          "must": [],
          "filter": [
            {
              "bool": {
                "should": [
                  {
                    "exists": {
                      "field": "layers.zbee_nwk.zbee_nwk_zbee_nwk_src64.keyword"
                    }
                  }
                ],
                "minimum_should_match": 1
              }
            }
          ],
          "should": [],
          "must_not": []
        }
      },
      "aggs": {
        "0-metric": {
          "top_metrics": {
            "metrics": {
              "field": "layers.zbee_nwk.zbee_nwk_zbee_nwk_src64.keyword"
            },
            "size": 1,
            "sort": {
              "timestamp": "desc"
            }
          }
        }
      }
    }
  },
  "size": 0,
}


def calulate_total_count(es):
    data = es.search(index='packetzapper', body=count_query)
    count = data["aggregations"]["unique_count"]["value"]
    return int(count)

def calulate_zr_count(es):
    data = es.search(index='packetzapper', body=zr_query)
    median = data["aggregations"]['0']["values"]["50.0"]
    return int((median-2)/3)


def calulate_zed_count(es):
    data = es.search(index='packetzapper', body=zed_query)
    count = data["aggregations"]["unique_count"]["value"]
    return int(count)


def calulate_zc_mac(es):
  data = es.search(index='packetzapper', body=ZC_query)
  mac = data["aggregations"]["0-bucket"]["0-metric"]["top"][0]["metrics"]['layers.zbee_nwk.zbee_nwk_zbee_nwk_src64.keyword']
  return mac