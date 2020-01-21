from datetime import timedelta
from couchbase.cluster import Cluster
from couchbase.collection import GetOptions
class Migrating(object):
    pass

#tag::timeoutbuilder[]
# SDK 3 equivalent
cluster=Cluster("couchbases://10.192.1.104")
collection=cluster.bucket("default").default_collection()
collection.timeout=5
#end::timeoutbuilder[]

# not applicable
#natag::shutdown[]
# ClusterEnvironment env = ClusterEnvironment.create();
# Cluster cluster = Cluster.connect(
#     "127.0.0.1",
#                   // pass the custom environment through the cluster options
# clusterOptions("user", "pass").environment(env)
# );
#
# // first disconnect, then shutdown the environment
# cluster.disconnect();
# env.shutdown();
#naend::shutdown[]


#natag::sysprops[]
# not applicable
# Will set the max http connections to 23
# System.setProperty("com.couchbase.env.io.maxHttpConnections", "23");
# Cluster.connect("127.0.0.1", "user", "pass");
#
# #This is equivalent to
# ClusterEnvironment env = ClusterEnvironment \
#     .builder() \
#     .ioConfig(IoConfig.maxHttpConnections(23)) \
#     .build();
#naend::sysprops[]

from couchbase.cluster import *
from couchbase_core.cluster import PasswordAuthenticator
from couchbase_v2 import COMPRESS_INOUT
#tag::connstr[]
# Will set the compression type to inout
Cluster.connect(
    "127.0.0.1?compression=inout",ClusterOptions(PasswordAuthenticator(
    "user",
    "pass")))

# This is equivalent to
collection.compression = COMPRESS_INOUT
#end::connstr[]

#natag::rbac[]
# add convenience overload when available
Cluster.connect("127.0.0.1", PasswordAuthenticator("username", "password"))
#naend::rbac[]

#tag::rbac-full[]
Cluster.connect(
    "127.0.0.1",
    ClusterOptions(PasswordAuthenticator("username", "password")))
#end::rbac-full[]

from couchbase_core.cluster import  CertAuthenticator
import os
#tag::certauth[]
cert_dir=os.path.join(os.path.curdir,"cert_dir")

Cluster.connect("127.0.0.1", ClusterOptions(
    CertAuthenticator(cert_path="cert.pem",
                      key_path="key.crt",
                      trust_store_path="trust_store.pem"
)))
#end::certauth[]

#tag::simpleget[]
cluster = Cluster.connect("127.0.0.1", ClusterOptions(PasswordAuthenticator("user", "pass")))
bucket = cluster.bucket("travel-sample")
collection = bucket.default_collection()

get_result = collection.get("airline_10")

#end::simpleget[]

Cluster cluster = Cluster.connect("127.0.0.1", "user", "pass");
Bucket bucket = cluster.bucket("travel-sample");
Collection collection = bucket.defaultCollection();

{
// #tag::upsertandget[]
MutationResult upsertResult = collection.upsert("mydoc-id", JsonObject.create());
GetResult getResult = collection.get("mydoc-id");
// #end::upsertandget[]
}

"""


    
    {
      // #tag::rawjson[]
      byte[] content = "{}".getBytes(StandardCharsets.UTF_8);
      MutationResult upsertResult = collection.upsert(
        "mydoc-id",
        content,
        upsertOptions().transcoder(RawJsonTranscoder.INSTANCE)
      );
      // #end::rawjson[]
    }

    {
      // #tag::customtimeout[]
      // SDK 3 custom timeout
      GetResult getResult = collection.get(
        "mydoc-id",
        getOptions().timeout(Duration.ofSeconds(5))
      );
      // #end::customtimeout[]
    }

    {
      // #tag::querysimple[]
      // SDK 3 simple query
      QueryResult queryResult = cluster.query("select * from `travel-sample` limit 10");
      for (JsonObject value : queryResult.rowsAsObject()) {
// ...
}
      // #end::querysimple[]
    }

    {
      // #tag::queryparameterized[]
      // SDK 3 named parameters
      cluster.query(
    "select * from bucket where type = $type",
        queryOptions().parameters(JsonObject.create().put("type", "airport"))
      );

      // SDK 3 positional parameters
      cluster.query(
    "select * from bucket where type = $1",
        queryOptions().parameters(JsonArray.from("airport"))
      );
      // #end::queryparameterized[]
}

    {
      // #tag::analyticssimple[]
      // SDK 3 simple analytics query
      AnalyticsResult analyticsResult = cluster.analyticsQuery("select * from dataset");
      for (JsonObject value : analyticsResult.rowsAsObject()) {
        // ...
}
      // #end::analyticssimple[]
    }

    {
      // #tag::analyticsparameterized[]
      // SDK 3 named parameters for analytics
      cluster.analyticsQuery(
        "select * from dataset where type = $type",
        analyticsOptions().parameters(JsonObject.create().put("type", "airport"))
      );

      // SDK 3 positional parameters for analytics
      cluster.analyticsQuery(
        "select * from dataset where type = $1",
        analyticsOptions().parameters(JsonArray.from("airport"))
      );
      // #end::analyticsparameterized[]
    }

    {
      // #tag::searchsimple[]
      // SDK 3 search query
      SearchResult searchResult = cluster.searchQuery(
    "indexname",
        SearchQuery.queryString("airports"),
        searchOptions()
          .timeout(Duration.ofSeconds(2))
          .limit(5)
          .fields("a", "b", "c")
);
      for (SearchRow row : searchResult.rows()) {
// ...
}
      // #end::searchsimple[]
    }

    {
      // #tag::searchcheck[]
      SearchResult searchResult = cluster.searchQuery(
        "myindex",
        SearchQuery.queryString("searchstring")
      );
      if (searchResult.metaData().errors().isEmpty()) {
        // no errors present, so full data got returned
      }
      // #end::searchcheck[]
    }

    {
      // #tag::viewquery[]
      // SDK 3 view query
      ViewResult viewResult = bucket.viewQuery(
        "design",
        "view",
        viewOptions().limit(5).skip(2).timeout(Duration.ofSeconds(10))
);
      for (ViewRow row : viewResult.rows()) {
                          // ...
}
      // #end::viewquery[]
    }
  }
}
"""