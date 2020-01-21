"""
"= Migrating from SDK2 to SDK3 API

:nav-title: Migrating to Python SDK 3.0 API
:page-topic-type: concept
:page-aliases: ROOT:migrate

[abstract]
The 3.0 API breaks the existing 2.0 APIs in order to provide a number of improvements.
Collections and Scopes are introduced.
The Document class and structure has been completely removed from the API, and the returned value is now `Result`.
Retry behaviour is more proactive, and lazy bootstrapping moves all error handling to a single place.
Individual behaviour changes across services are explained here.


include::partial$beta-warning.adoc[]


include::6.5@sdk:shared:partial$migration.adoc[tag=intro]


include::6.5@sdk:shared:partial$migration.adoc[tag=terms]

As an example here is a KeyValue document fetch:

// change to $Your_language
[source,python]
----
"""
from datetime import timedelta
from couchbase.cluster import Cluster
cluster=Cluster("couchbases://10.192.1.104")
collection=cluster.default_collection()
get_result = collection.get("key", GetOptions(timeout=timedelta(seconds=3)))
"""
----

Compare this to a N1QL query:

// change to $Your_language
[source,python]
----
query_result = cluster.query("select 1=1", QueryOptions(timeout=timedelta(seconds=3))
                             ----

include::6.5@sdk:shared:partial$migration.adoc[tag=terms2]


include::6.5@sdk:shared:partial$migration.adoc[tag=new]


include::6.5@sdk:shared:partial$migration.adoc[tag=lang]




// Outline below for individual SDKs -- please expand as appropriate, many topics can be covered lightly
//
// Please use before(2.n) / after (3.0) snippets in all cases where it is helpful
// (probably nearly everywhere, I'm afraid)


===  Installation and Configuration

- where to get the new artifacts / vs old place

The Python SDK 3.x is available for download from the same resources as the previous generation. Builds can be found on PyPi.
Please see the xref:sdk-release-notes.adoc[Release Notes] for up-to-date information.

                                                                         - discuss new dependencies if needed
- discuss configuration old and new, especially if certain
custom options are not present anymore (why they are not used)
and how users might want to transfer this config over to the
new one
- discuss cert auth
- discuss encryption config

IMPORTANT: Java SDK 3.x has a minimum required Java version of 8, although we recommend running the latest LTS version (i.e. at the time of writing JDK 11) with the highest patch version available.

Note that the transitive dependency list has changed.
As a refresher, Java SDK 2 depended on the following artifacts:

    * com.couchbase.client:**core-io**
                             * io.reactivex:**rxjava**
                                              * io.opentracing:**opentracing-api**

                                                                 SDK 3 depends on the following ones instead:

* com.couchbase.client:**core-io**
                         * io.projectreactor:**reactor-core**
                                               * org.reactivestreams:**reactive-streams**

                                                                       Note that the SDK now uses `Reactor` instead of `RxJava` and the explicit dependency on `OpenTracing` is gone.
    We are now providing support for different tracing backends with additional dependencies that can be pulled in as needed.
`ReactiveStreams` is a transitive dependency of `Reactor` and provides interoperability code so you can use other reactive streams implementations as well.

If you are pulling in the SDK through a package manager (recommended), all dependencies will be resolved for you automatically.
Otherwise please download the zip file and adjust your jar files accordingly.


=== Configuring the Environment

The fundamental semantics of the `CouchbaseEnvironment` from SDK 2 remain the same, although somewhat more flexible, with its configuration cleaned up to be more easily discoverable.
The `CouchbaseEnvironment` has been renamed to `ClusterEnvironment` and can be customized through a builder:

    [source,java]
    ----
    // SDK 2 custom KV timeout
CouchbaseEnvironment env = DefaultCouchbaseEnvironment \
    .builder() \
    .kvTimeout(TimeUnit.SECONDS.toMillis(5)) \
    .build();
----

[source,java]
----
include::example$Migrating.java[tag=timeoutbuilder,indent=0]
----

Similar to SDK 2, if you create your own `ClusterEnvironment` the SDK will not shut it down for you -- you need to do this manually at the end of the program lifetime:

    [source,java]
    ----
    include::example$Migrating.java[tag=shutdown,indent=0]
----

If no custom environment is passed in, the default settings can still be customized through either the connection string or xref:ref:client-settings.adoc[system properties].
The SDK has elaborate reflection logic in place to parse "flat" string values and apply them to the builder, which means that you can now configure more properties than in SDK 2.
Note that the property paths have changed.

                                  [source,java]
                                  ----
include::example$Migrating.java[tag=sysprops,indent=0]
----

[source,java]
----
include::example$Migrating.java[tag=connstr,indent=0]
----

The paths for each config start with the pattern `com.couchbase.env.` followed by either a toplevel or nested config. `IoConfig` is under the `io` path, similar to `TimeoutConfig` under `timeout`.
So, if you want to modify a KV timeout you can use the `com.couchbase.env.timeout.kvTimeout` path.
See the xref:ref:client-settings.adoc[configuration section] for full specifics.

        At the end of this guide you'll find a xref:#configurations-options-reference[reference] that describes the SDK 2 environment options and their SDK 3 equivalents where applicable.


=== Authentication

Since SDK 2 supports Couchbase Server clusters older than 5.0, it had to support both Role-Based access control as well as bucket-level passwords.
The minimum cluster version supported by SDK 3 is Server 5.0, which means that only RBAC is supported.
This is why you can set the username and password when directly connecting:

    [source,java]
    ----
    include::example$Migrating.java[tag=rbac,indent=0]
----

This is just a shorthand for:

    [source,java]
    ----
    include::example$Migrating.java[tag=rbac-full,indent=0]
----

The reason why you can pass in a specific authenticator is that you can also use the same approach to configure certificate-based authentication:


[source,java]
----
include::example$Migrating.java[tag=certauth,indent=0]
----

Please see the xref:howtos:authentication.adoc[documentation on certificate-based authentication] for detailed information on how to configure this properly.


== Connection Lifecycle

- discuss bootstrapping
- important: bootstrapping is now "lazy" so also discuss how to do the eager
checks and any impact it might have on the first op being slow?
- discuss shutdown
          - if external state is passed in optionally, discuss
management of this state
                   - discuss the impact of 6.5 "gcccp" and cluster level queries
                                                                         - SASL by default on non-PLAIN (if applicable)


From a high-level perspective, bootstrapping and shutdown is very similar to SDK 2.
One notable difference is that the `Collection` is introduced and that the individual methods like `bucket` immediately return, and do not throw an exception.
Compare SDK 2: the `openBucket` method would not work if it could not open the bucket.

The reason behind this change is that even if a bucket can be opened, a millisecond later it may not be available any more.
All this state has been moved into the actual operation so there is only a single place where the error handling needs to take place.
This simplifies error handling and retry logic for an application.

In SDK 2, you connected, opened a bucket, performed a KV op, and disconnected like this:

[source,java]
----
Cluster cluster = CouchbaseCluster.create("127.0.0.1");
cluster.authenticate("user", "pass");
Bucket bucket = cluster.openBucket("travel-sample");

JsonDocument getResult = bucket.get("airline_10");

cluster.disconnect();
----

Here is the SDK 3 equivalent:

[source,java]
----
include::example$Migrating.java[tag=simpleget,indent=0]
----

`Collections` will be generally available with an upcoming Couchbase Server release, but the SDK already encodes it in its API to be future-proof.
If you are using a Couchbase Server version which does not support `Collections`, always use the `defaultCollection()` method to access the KV API; it will map to the full bucket.

IMPORTANT: You'll notice that `bucket(String)` returns immediately, even if the bucket resources are not completely opened.
This means that the subsequent `get` operation may be dispatched even before the socket is open in the background.
The SDK will handle this case transparently, and reschedule the operation until the bucket is opened properly.
This also means that if a bucket could not be opened (say, because no server was reachable) the operation will time out.
Please check the logs to see the cause of the timeout (in this case, you'll see socket connect rejections).

Also note, you will now find Query, Search, and Analytics at the `Cluster` level.
                                                                               This is where they logically belong.
    If you are using Couchbase Server 6.5 or later, you will be able to perform cluster-level queries even if no bucket is open.
    If you are using an earlier version of the cluster you must open at least one bucket, otherwise cluster-level queries will fail.


                                                                                                                               === Serialization and Transcoding

                                                                                                                                   - describe how it works for your language, how to override and any platform-specific
encoding and decoding guidelines.
- Also important how to convert from the document types to the new approach

In SDK 2 the main method to control transcoding was through providing different `Document` instances (which in turn had their own transcoder associated), such as the `JsonDocument`.
This only worked for the KV APIs though -- Query, Search, Views, and other services exposed their JSON rows/hits in different ways.
All of this has been unified in SDK 3 under a single concept: serializers and transcoders.

    By default, all KV APIs transcode to and from JSON -- you can also provide java POJOs which you couldn't in the past.
`JsonObject` and `JsonArray` are still available, like in SDK 2:

[source,java]
----
// SDK 2 upsert and get
JsonDocument upsertResult = bucket.upsert(
    JsonDocument.create("mydoc-id", JsonObject.empty())
);
JsonDocument getResult = bucket.get("mydoc-id");
----

[source,java]
----
include::example$Migrating.java[tag=upsertandget,indent=0]
----

If you want to write already-encoded JSON, instead of using the `RawJsonDocument` you now need to use the `RawJsonTranscoder.INSTANCE`:

[source,java]
----
include::example$Migrating.java[tag=rawjson,indent=0]
----

Here is a mapping table from the SDK 2 `Document` types to the new transcoder types:

.SDK 2.x Document vs. SDK 3.x Transcoder
[options="header"]
|=======================
| SDK 2                          | SDK 3
                                       |`JsonDocument`                  | `JsonTranscoder` (default)
                                       |`JsonArrayDocument`             | `JsonTranscoder` (default)
                                       |`JsonBooleanDocument`           | `JsonTranscoder` (default)
                                       |`JsonLongDocument`              | `JsonTranscoder` (default)
                                       |`JsonStringDocument`            | `JsonTranscoder` (default)
                                       |`JsonDoubleDocument`            | `JsonTranscoder` (default)
                                       |`LegacyDocument`                | removed
                                       |`RawJsonDocument`               | `RawJsonTranscoder`
                                       |`SerializableDocument`          | removed
                                       |`StringDocument`                | `RawStringTranscoder`
                                       |`ByteArrayDocument`             | `RawBinaryTranscoder`
                                       |`BinaryDocument`                | `RawBinaryTranscoder`
                                       |`EntityDocument`                | `JsonTranscoder` (default)
|=======================

The `LegacyDocument` in SDK 2 was in place to support SDK 1, so it has been removed.
                                                                                Serializers and transcoders can also be customized and overwritten on a per-operation basis, please see the appropriate documentation section for details.

The JSON `Transcoders` use a `Serializer` underneath.
While a transcoder can handle many different storage types, the serializer is specialized for JSON encoding and decoding.
On all JSON-only APIs (i.e. Sub-doc, Query, Search,...) you'll only find a `Serializer`, not a `Transcoder`, in the operation options.
Usually there is no need to override it unless you want to provide your own implementation (i.e. if you have your own POJO mapping json logic in place, and want to reuse it).


== Exception Handling

- discuss new exception hierachy in principle and how users should
approach it when migrating
- explain maybe new error handling strategies that are in place,
around retry strategies especially and their behavior

How to _handle_ exceptions is unchanged from SDK 2.
You should still use `try/catch` on the blocking APIs and the corresponding reactive/async methods on the other APIs.
There have been changes made in the following areas:

- Exception hierachy and naming.
- Proactive retry where possible.


=== Exception hierachy

The exception hierachy is now flat and unified under a `CouchbaseException`.
Each `CouchbaseException` has an associated `ErrorContext` which is populated with as much info as possible and then dumped alongside the stack trace if an error happens.

Here is an example of the error context if a N1QL query is performed with an invalid syntax (i.e. `select 1= from`):

[source]
----
Exception in thread "main" com.couchbase.client.core.error.ParsingFailedException: Parsing of the input failed {"completed":true,"coreId":1,"errors":[{"code":3000,"message":"syntax error - at from"}],"idempotent":false,"lastDispatchedFrom":"127.0.0.1:62253","lastDispatchedTo":"127.0.0.1:8093","requestId":3,"requestType":"QueryRequest","retried":11,"retryReasons":["ENDPOINT_TEMPORARILY_NOT_AVAILABLE","BUCKET_OPEN_IN_PROGRESS"],"service":{"operationId":"9111b961-e585-42f2-9cab-e1501da7a40b","statement":"select 1= from","type":"query"},"timeoutMs":75000,"timings":{"dispatchMicros":15599,"totalMicros":1641134}}
----

The expectation is that the application catches the `CouchbaseException` and deals with it as an unexpected error
(e.g. logging with subsequent bubbling up of the exception or failing).
In addition to that, each method exposes exceptions that can be caught separately if needed.
As an example, consider the javadoc for the `Collection.get` API:

[source]
----
...
* @throws DocumentNotFoundException the given document id is not found in the collection.
* @throws TimeoutException if the operation times out before getting a result.
* @throws CouchbaseException for all other error reasons (acts as a base type and catch-all).
...
----

These exceptions extend `CouchbaseException`, but both the `TimeoutException` and the `DocumentNotFoundException` can be caught individually if specific logic should be executed to handle them.

=== Proactive Retry

One reason why the APIs do not expose a long list of exceptions is that the SDK now retries as many operations as it can if it can do so safely.
This depends on the type of operation (idempotent or not), in which state of processing it is (already dispatched or not), and what the actual response code is if it arrived already.
As a result, many transient cases -- such as locked documents, or temporary failure -- are now retried by default and should less often impact applications.
It also means, when migrating to the new SDK API, you may observe a longer period of time until an error is returned by default.

NOTE: Operations are retried by default as described above with the default `BestEffortRetryStrategy`.
Like in SDK 2 you can configure fail-fast retry strategies to not retry certain or all operations.
The `RetryStrategy` interface has been extended heavily in SDK 3 -- please see the xref:howtos:error-handling.adoc[error handling documentation].

When migrating your SDK 2 exception handling code to SDK 3, make sure to wrap every call with a catch for `CouchbaseException` (or let it bubble up immediately).
You can likely remove your user-level retry code for temporary failures, backpressure exception, and so on.
One notable exception from this is the `CasMismatchException`, which is still thrown since it requires more app-level code to handle (most likely identical to SDK 2).


=== Logging and Events

- discuss any changes to the logging infrastructure or event system if made


Configuring and consuming logs has not greatly changed.
The SDK still uses _SLF4J_, if found on the classpath, and if not reverts back to the JDK logger (it can also be configured to log to `stderr` instead).
The big difference is that the `EventBus` (also present in SDK 2) has been made much more powerful -- and all logs are sent as events through it.
The `LoggingEventConsumer` being one of the potential consumers, and turning events into log lines.

The biggest impact you'll see from it is that the log messages now look very structured and contain contextual information where possible.

[source]
----
13:36:46 INFO  [com.couchbase.node:470] [com.couchbase.node][NodeConnectedEvent] Node connected {"coreId":1,"managerPort":"8091","remote":"127.0.0.1"}
13:36:46 INFO  [com.couchbase.core:470] [com.couchbase.core][BucketOpenedEvent][393161µs] Opened bucket "travel-sample" {"coreId":1}
----

Notice the package path (which you can also filter on if needed), the event name, an optional time that it took to perform the operation, the message and surrounding context.
This makes it easier to debug potential problems but also allows consuming all the events and feeding them in other monitoring systems without having to round-trip a file log.
Please see xref:howtos:collecting-information-and-logging.adoc[the logging documentation] for further information.


===  Migrating Services

- one section for each service that goes in-depth on each command
and discusses old vs. new

The following section discusses each service in detail and covers specific bits that have not been covered by the more generic sections above.

==== Key Value

- don't forget the get replica changes!


The Key/Value (KV) API is now located under the `Collection` interface, so even if you do not use collections, the `defaultCollection()` needs to be opened in order to access it.

The following table describes the SDK 2 KV APIs and where they are now located in SDK 3:

.SDK 2.x KV API vs. SDK 3.x KV API
[options="header"]
|====
| SDK 2                          | SDK 3
|`Bucket.upsert`                 | `Collection.upsert`
|`Bucket.get`                    | `Collection.get`
|`Bucket.exists`                 | `Collection.exists`
|`Bucket.getFromReplica`         | `Collection.getAnyReplica` and `Collection.getAllReplicas`
|`Bucket.getAndLock`             | `Collection.getAndLock`
|`Bucket.getAndTouch`            | `Collection.getAndTouch`
|`Bucket.insert`                 | `Collection.insert`
|`Bucket.upsert`                 | `Collection.upsert`
|`Bucket.replace`                | `Collection.replace`
|`Bucket.remove`                 | `Collection.remove`
|`Bucket.unlock`                 | `Collection.unlock`
|`Bucket.touch`                  | `Collection.touch`
|`Bucket.lookupIn`               | `Collection.lookupIn`
|`Bucket.mutateIn`               | `Collection.mutateIn`
|`Bucket.counter`                | `BinaryCollection.increment` and `BinaryCollection.decrement`
|`Bucket.append`                 | `BinaryCollection.append`
|`Bucket.prepend`                | `BinaryCollection.prepend`
|====

In addition, the datastructure APIs have been renamed and moved:

.Datastructure API Changes
[options="header"]
|====
| SDK 2                   | SDK 3
|`Bucket.mapAdd`                 | `Collection.map`
|`Bucket.mapGet`                 | `Collection.map`
|`Bucket.mapRemove`              | `Collection.map`
|`Bucket.mapSize`                | `Collection.map`
|`Bucket.listGet`                | `Collection.list`
|`Bucket.listAppend`             | `Collection.list`
|`Bucket.listRemove`             | `Collection.list`
|`Bucket.listPrepend`            | `Collection.list`
|`Bucket.listSet`                | `Collection.list`
|`Bucket.listSize`               | `Collection.list`
|`Bucket.setAdd`                 | `Collection.set`
|`Bucket.setContains`            | `Collection.set`
|`Bucket.setRemove`              | `Collection.set`
|`Bucket.setSize`                | `Collection.set`
|`Bucket.queuePush`              | `Collection.queue`
|`Bucket.queuePop`               | `Collection.queue`
|====

There are two important API changes:

* On the request side, overloads have been reduced and moved under a `Options` block
* On the response side, the return types have been unified.

The signatures now look very similar.
The concept of the `Document` as a type is gone in SDK 3 and instead you need to pass in the properties explicitly.
This makes it very clear what is returned, especially on the response side.

Thus, the `get` method does not return a `Document` but a `GetResult` instead, and the `upsert` does not return a `Document` but a `MutationResult`.
Each of those results only contains the field that the specific method can actually return, making it impossible to accidentally try to access the `expiry` on the `Document` after a mutation, for example.

Instead of having many overloads, all optional params are now part of the `Option` block.
All required params are still part of the method signature, making it clear what is required and what is not (or has default values applied if not overridden).

The timeout can be overridden on every operation and now takes a `Duration` from java 8.
Compare SDK 2 and SDK 3 custom timeout setting:

[source,java]
----
// SDK 2 custom timeout
bucket.get("mydoc-id", 5, TimeUnit.SECONDS);
----

[source,java]
----
include::example$Migrating.java[tag=customtimeout,indent=0]
----

In SDK 2, the `getFromReplica` method had a `ReplicaMode` argument which allowed to customize its behavior on how many replicas should be reached.
We have identified this as a potential source of confusion and as a result split it up in two methods that simplify usage significantly.
There is now a `getAllReplicas` method and a `getAnyReplica` method.

* `getAllReplicas` asks the active node and all available replicas and returns the results as a stream.
* `getAnyReplica` uses `getAllReplicas`, and returns the first result obtained.

Unless you want to build some kind of consensus between the different replica responses, we recommend `getAnyReplica` for a fallback to a regular `get` when the active node times out.

NOTE: Operations which cannot be performed on JSON documents have been moved to the `BinaryCollection`, accessible through `Collection.binary()`.
These operations include `append`, `prepend`, `increment`, and `decrement` (previously called `counter` in SDK 2).
These operations should only be used against non-json data.
Similar functionality is available through `mutateIn` on JSON documents.

=== Query

N1QL querying is now available at the `Cluster` level instead of the bucket level, because you can also write N1QL queries that span multiple buckets. Compare a simple N1QL query from SDK 2 with its SDK 3 equivalent:

[source,java]
----
// SDK 2 simple query
N1qlQueryResult queryResult = bucket.query(N1qlQuery.simple("select * from `travel-sample` limit 10"));
for (N1qlQueryRow row : queryResult) {
    JsonObject value = row.value();
// ...
}
----

[source,java]
----
include::example$Migrating.java[tag=querysimple,indent=0]
----

Note that there is no `N1qlQuery.simple` any more -- parameter option have been moved to the `queryOptions()` for consistency reasons.
    The following shows how to do named and positional parameters in SDK 2, and their SDK 3 counterparts:

[source,java]
----
// SDK 2 named parameters
bucket.query(N1qlQuery.parameterized(
    "select * from bucket where type = $type",
    JsonObject.create().put("type", "airport")
));

// SDK 2 positional parameters
bucket.query(N1qlQuery.parameterized(
    "select * from bucket where type = $1",
    JsonArray.from("airport")
));
----

[source,java]
----
include::example$Migrating.java[tag=queryparameterized,indent=0]
----

If you want to use prepared statements, the `adhoc()` method is still available on the `QueryOptions`, alongside every other option that used to be exposed on the SDK 2 Query options.

Much of the non-row metadata has been moved into a specific `QueryMetaData` section:

.Query Metadata Changes
[options="header"]
|====
| SDK 2                             | SDK 3
|`N1qlQueryResult.signature`        | `QueryResult.metaData.signature`
|`N1qlQueryResult.info`             | `QueryResult.metaData.metrics`
|`N1qlQueryResult.profileInfo`      | `QueryResult.metaData.profile`
|`N1qlQueryResult.parseSuccess`     | removed
|`N1qlQueryResult.finalSuccess`     | removed
|`N1qlQueryResult.status`           | `QueryResult.metaData.status`
|`N1qlQueryResult.errors`           | throws an Exception on `QueryResult`
|`N1qlQueryResult.requestId`        | `QueryResult.metaData.requestId`
|`N1qlQueryResult.clientContextId`  | `QueryResult.metaData.clientContextId`
|====

It is no longer necessary to check for a specific error in the stream: if an error happened during processing it will throw an exception at the top level of the query.
The reactive streaming API will terminate the rows' `Flux` with an exception as well as soon as it is discovered.
This makes error handling much easier in both the blocking and non-blocking cases.

While in SDK 2 you had to manually check for errors (otherwise you'd get an empty row collection):

[source,java]
----
N1qlQueryResult queryResult = bucket.query(N1qlQuery.simple("select 1="));
if (!queryResult.errors().isEmpty()) {
// errors contain [{"msg":"syntax error - at end of input","code":3000}]
}
----

In SDK 3 the top level `query` method will throw an exception:

[source]
----
Exception in thread "main" com.couchbase.client.core.error.ParsingFailedException: Parsing of the input failed {"completed":true,"coreId":1,"errors":[{"code":3000,"message":"syntax error - at end of input"}],"idempotent":false,"lastDispatchedFrom":"127.0.0.1:51703","lastDispatchedTo":"127.0.0.1:8093","requestId":5,"requestType":"QueryRequest","retried":0,"service":{"operationId":"1c623a77-196a-4890-96cd-9d4f3f596477","statement":"select 1=","type":"query"},"timeoutMs":75000,"timings":{"dispatchMicros":13798,"totalMicros":70789}}
at com.couchbase.client.java.AsyncUtils.block(AsyncUtils.java:51)
at com.couchbase.client.java.Cluster.query(Cluster.java:225)
----

Not only does it throw a `CouchbaseException`, it also tries to map it to a specific exception type and include extensive contextual information for a better troubleshooting experience.

=== Analytics

Analytics querying, like N1QL, is also moved to the `Cluster` level: it is now accessible through the `Cluster.analyticsQuery` method.
    As with the Query service, parameters for the Analytics queries have moved into the `AnalyticsOptions`:

    [source,java]
    ----
    include::example$Migrating.java[tag=analyticssimple,indent=0]
----

[source,java]
----
include::example$Migrating.java[tag=analyticsparameterized,indent=0]
----

Also, errors will now be thrown as top level exceptions and it is no longer necessary to explicitly check for errors:

    [source,java]
    ----
    // SDK 2 error check
AnalyticsQueryResult analyticsQueryResult = b1.query(AnalyticsQuery.simple("select * from foo"));
if (!analyticsQueryResult.errors().isEmpty()) {
                                              // errors contain [{"msg":"Cannot find dataset foo in dataverse Default nor an alias with name foo! (in line 1, at column 15)","code":24045}]
}
----

[source]
----
// SDK 3 top level exception
com.couchbase.client.core.error.DatasetNotFoundException: The analytics dataset is not found {"completed":true,"coreId":1,"errors":[{"code":24045,"message":"Cannot find dataset foo in dataverse Default nor an alias with name foo! (in line 1, at column 15)"}],"idempotent":false,"lastDispatchedFrom":"127.0.0.1:51942","lastDispatchedTo":"127.0.0.1:8095","requestId":5,"requestType":"AnalyticsRequest","retried":0,"service":{"operationId":"80265061-62e0-4c35-860f-a07a97e1a5ee","priority":0,"statement":"select * from foo","type":"analytics"},"timeoutMs":75000,"timings":{"dispatchMicros":27005,"totalMicros":89888}}
at com.couchbase.client.java.AsyncUtils.block(AsyncUtils.java:51)
at com.couchbase.client.java.Cluster.analyticsQuery(Cluster.java:250)
----

=== Search

The Search API has changed a bit in SDK 3 so that it aligns with the other query APIs.
The type of queries have stayed the same, but all optional parameters moved into `SearchOptions`.
Also, similar to the other query APIs, it is now available at the `Cluster` level.

Here is a SDK 2 Search query with some options, and its SDK 3 equivalent:

    [source,java]
    ----
    //  SDK 2 search query
SearchQueryResult searchResult = bucket.query(new SearchQuery(
    "indexname",
    SearchQuery.queryString("airports")).limit(5).fields("a", "b", "c"),
                                                  2,
                                                  TimeUnit.SECONDS
);
for (SearchQueryRow row : searchResult.hits()) {
// ...
}
----

[source,java]
----
include::example$Migrating.java[tag=searchsimple,indent=0]
----

Error handling for streaming is handled differently.
        While fatal errors will still raise top-level exceptions, any errors that happend during streaming (for example if one node is down, and only partial results are returned) they will not terminate the result.
The reasoning behind this is that usually with search results, having partial results is better than none.

Here is a top level exception, for _the index does not exist_:

[source]
----
com.couchbase.client.core.error.SearchIndexNotFoundException: The search index is not found on the server {"completed":true,"coreId":1,"httpStatus":400,"idempotent":true,"lastDispatchedFrom":"127.0.0.1:53280","lastDispatchedTo":"127.0.0.1:8094","requestId":5,"requestType":"SearchRequest","retried":0,"service":{"indexName":"myindex","type":"search"},"status":"INVALID_ARGS","timeoutMs":75000,"timings":{"dispatchMicros":12741,"totalMicros":66262}}
at com.couchbase.client.java.AsyncUtils.block(AsyncUtils.java:51)
at com.couchbase.client.java.Cluster.searchQuery(Cluster.java:275)
----

If you want to be absolutely sure that you didn't get only partial data, you can check the error map:

[source,java]
----
include::example$Migrating.java[tag=searchcheck,indent=0]
----

=== Views

Views have stayed at the `Bucket` level, because it does not have the concept of collections and is scoped at the bucket level on the server as well.
The API has stayed mostly the same, the most important change is that `staleness` is unified under the `ViewConsistency` enum.

.View Staleness Mapping
[options="header"]
|====
| SDK 2                             | SDK 3
|`Stale.TRUE`                       | `ViewScanConsistency.NOT_BOUNDED`
|`Stale.FALSE`                      | `ViewScanConsistency.REQUEST_PLUS`
|`Stale.UPDATE_AFTER`               | `ViewScanConsistency.UPDATE_AFTER`
|====

Compare this SDK 2 view query with its SDK 3 equivalent:

[source,java]
----
// SDK 2 view query
ViewResult query = bucket.query(
    ViewQuery.from("design", "view").limit(5).skip(2),
                  10,
                  TimeUnit.SECONDS
);
for (ViewRow row : query) {
                          // ...
}
----

[source,java]
----
include::example$Migrating.java[tag=viewquery,indent=0]
----

Exceptions are exclusively raised at the top level: for example, if the design document is not found:

[source]
----
com.couchbase.client.core.error.ViewNotFoundException: The queried view is not found on the server {"completed":true,"coreId":1,"httpStatus":404,"idempotent":true,"lastDispatchedFrom":"127.0.0.1:53474","lastDispatchedTo":"127.0.0.1:8092","requestId":5,"requestType":"ViewRequest","retried":0,"service":{"bucket":"travel-sample","designDoc":"foo","development":false,"type":"views","viewName":"bar"},"status":"NOT_FOUND","timeoutMs":75000,"timings":{"dispatchMicros":77572,"totalMicros":189389},"viewError":"not_found","viewErrorReason":"Design document _design/foo not found"}
at com.couchbase.client.java.AsyncUtils.block(AsyncUtils.java:51)
at com.couchbase.client.java.Bucket.viewQuery(Bucket.java:182)

----

== Management APIs

- discusses how to migrate from each old management api to the new one
- where it is found, what exceptions it throws, etc.


In SDK 2, the management APIs were centralized in the `ClusterManager` at the cluster level and the `BucketManager` at the bucket level.
Since SDK 3 provides more management APIs, they have been split up in their respective domains.
So for example when in SDK 2 you needed to remove a bucket you would call `ClusterManager.removeBucket` you will now find it under `BucketManager.dropBucket`.
Also, creating a N1QL index now lives in the `QueryIndexManager`, which is accessible through the `Cluster`.

The following table provides a mapping from the SDK 2 management APIs to those of SDK 3:

.SDK 2.x vs SDK 3.x ClusterManager
[options="header"]
|====
| SDK 2                          | SDK 3
|`ClusterManager.info`           | removed
|`ClusterManager.getBuckets`     | `BucketManager.getAllBuckets`
|`ClusterManager.getBucket`      | `BucketManager.getBucket`
|`ClusterManager.hasBucket`      | removed
|`ClusterManager.insertBucket`   | `BucketManager.createBucket`
|`ClusterManager.updateBucket`   | `BucketManager.updateBucket`
|`ClusterManager.removeBucket`   | `BucketManager.dropBucket`
|`ClusterManager.upsertUser`     | `UserManager.upsertUser`
|`ClusterManager.removeUser`     | `UserManager.dropUser`
|`ClusterManager.getUsers`       | `UserManager.getAllUsers`
|`ClusterManager.getUser`        | `UserManager.getUser`
|`ClusterManager.apiClient`      | removed
|====

.SDK 2.x vs SDK 3.x BucketManager
[options="header"]
|====
| SDK 2                                    | SDK 3
|`BucketManager.info`                      | removed
|`BucketManager.flush`                     | `BucketManager.flushBucket`
|`BucketManager.getDesignDocuments`        | `ViewIndexManager.getAllDesignDocuments`
|`BucketManager.getDesignDocument`         | `ViewIndexManager.getDesignDocument`
|`BucketManager.insertDesignDocument`      | `ViewIndexManager.upsertDesignDocument`
|`BucketManager.upsertDesignDocument`      | `ViewIndexManager.upsertDesignDocument`
|`BucketManager.removeDesignDocument`      | `ViewIndexManager.dropDesignDocument`
|`BucketManager.publishDesignDocument`     | `ViewIndexManager.publishDesignDocument`
|`BucketManager.listN1qlIndexes`           | `QueryIndexManager.getAllIndexes`
|`BucketManager.createN1qlIndex`           | `QueryIndexManager.createIndex`
|`BucketManager.createN1qlPrimaryIndex`    | `QueryIndexManager.createPrimaryIndex`
|`BucketManager.dropN1qlIndex`             | `QueryIndexManager.dropIndex`
|`BucketManager.dropN1qlPrimaryIndex`      | `QueryIndexManager.dropPrimaryIndex`
|`BucketManager.buildN1qlDeferredIndexes`  | `QueryIndexManager.buildDeferredIndexes`
|`BucketManager.watchN1qlIndexes`          | `QueryIndexManager.watchIndexes`
|====

Extra Java stuff to be ported if possible



== Reactive and Async APIs

The move to Java 8 as a baseline has opened the door to expose `CompletableFuture` in addition to a reactive API.
You can now find it under the `async()` namespace of each level (for example, `Cluster.async()` -> `AsyncCluster`).
We also moved from `RxJava` to `Reactor` because it provides native Java 8 support and better performance out of the box.
`Reactor` has a growing community, and integrates very well into the Spring ecosystem.
The reactive API can now be found under the `reactive()` namespace (for example, `Collection.reactive()` -> `ReactiveCollection`).

Like in SDK 2, the async and reactive APIs provide the same functionality as their blocking counterpart.
There are only a couple places in the SDK where it does not make sense (such as the blocking datastructure APIs, which at the collection level implement the Java interfaces which do not have async or reactive counterparts).

IMPORTANT: if you need to use non-blocking APIs, we recommend using the reactive one.
The async API based on `CompletableFuture` should only be used as a building block for higher level abstractions, or if you absolutely need the last drop of performance.
The `Flux` and `Mono` types of reactor are very powerful and allow you to build efficient and flexible domain logic without blocking.

Since `Reactor` implements the reactive stream specification, you can still use `RxJava` through the interoperability interfaces.
This is out of scope for the migration guide -- please consult the reactor and rxjava documentations for further information.

As a starting point, the following types are comparable:

.SDK Reactor vs RxJava
[options="header"]
|====
| SDK 2 RxJava          | SDK 3 Reactor
|`Observable<T>`        | `Flux<T>`
|`Single<T>`            | `Mono<T>`
|`Completable`          | `Mono<Void>`
|====


== Configuration Options Reference

The following table provides commonly used configuration options in SDK 2 and where they can be now applied in SDK 3.
Note that some options have been removed, and others have different ways to configure them.

.SDK 2.x vs SDK 3.x Environment Configs
[options="header"]
|====
| SDK 2                        | SDK 3
|`sslEnabled`                  | `SecurityConfig.enableTls`
|`sslKeystoreFile`             | on `CertificateAuthenticator`
|`sslKeystorePassword`         | on `CertificateAuthenticator`
|`sslKeystore`                 | on `CertificateAuthenticator`
|`sslTruststoreFile`           | `SecurityConfig.trustCertificate`
|`sslTruststorePassword`       | `SecurityConfig.trustCertificate`
|`sslTruststore`               | `SecurityConfig.trustManagerFactory`
|`bootstrapCarrierEnabled`     | removed
|`bootstrapHttpDirectPort`     | via custom `SeedNode`
|`bootstrapHttpSslPort`        | via custom `SeedNode`
|`bootstrapCarrierDirectPort`  | via custom `SeedNode`
|`bootstrapCarrierSslPort`     | via custom `SeedNode`
|`ioPoolSize`                  | via custom `IoEnvironment` pools
|`computationPoolSize`         | removed
|`requestBufferSize`           | removed
|`responseBufferSize`          | removed
|`kvEndpoints`                 | `IoConfig.numKvConnections`
|`viewEndpoints`               | `IoConfig.maxHttpConnections`
|`queryEndpoints`              | `IoConfig.maxHttpConnections`
|`searchEndpoints`             | `IoConfig.maxHttpConnections`
|`userAgent`                   | removed
|`packageNameAndVersion`       | removed
|`observeIntervalDelay`        | removed
|`reconnectDelay`              | removed
|`retryDelay`                  | removed
|`ioPool`                      | via custom `IoEnvironment` pools
|`kvIoPool`                    | via custom `IoEnvironment` pools
|`viewIoPool`                  | via custom `IoEnvironment` pools
|`queryIoPool`                 | via custom `IoEnvironment` pools
|`searchIoPool`                | via custom `IoEnvironment` pools
|`analyticsIoPool`             | via custom `IoEnvironment` pools
|`scheduler`                   | `scheduler`
|`retryStrategy`               | `retryStrategy`
|`maxRequestLifetime`          | removed
|`keepAliveInterval`           | removed
|`autoreleaseAfter`            | removed
|`eventBus`                    | `eventBus`
|`bufferPoolingEnabled`        | removed
|`tcpNodelayEnabled`           | `IoConfig.enableTcpKeepAlives`
|`mutationTokensEnabled`       | `IoConfig.enableMutationTokens`
|`runtimeMetricsCollectorConfig`         | removed
|`networkLatencyMetricsCollectorConfig`  | removed
|`defaultMetricsLoggingConsumer`         | removed
|`socketConnectTimeout`        | removed
|`callbacksOnIoPool`           | removed
|`requestBufferWaitStrategy`   | removed
|`memcachedHashingStrategy`    | removed
|`keyValueServiceConfig`       | removed
|`viewServiceConfig`           | removed
|`queryServiceConfig`          | removed
|`searchServiceConfig`         | removed
|`analyticsServiceConfig`      | removed
|`configPollInterval`          | removed
|`configPollFloorInterval`     | removed
|`certAuthEnabled`             | on `CertificateAuthenticator`
|`continuousKeepAliveEnabled`  | removed
|`keepAliveErrorThreshold`     | removed
|`keepAliveTimeout`            | removed
|`couchbaseCoreSendHook`       | removed
|`forceSaslPlain`              | on `PasswordAuthenticator.allowedSaslMechanisms`
|`operationTracingEnabled`     | removed
|`operationTracingServerDurationEnabled`  | removed
|`tracer`                      | `requestTracer`
|`compressionMinSize`          | `CompressionConfig.minSize`
|`compressionMinRatio`         | `CompressionConfig.minRatio`
|`compressionEnabled`          | `CompressionConfig.enable`
|`orphanResponseReportingEnabled`         | removed
|`orphanResponseReporter`                 | removed
|`networkResolution`           | `IoConfig.networkResolution`
|`managementTimeout`           | `TimeoutConfig.managementTimeout`
|`queryTimeout`                | `TimeoutConfig.queryTimeout`
|`kvTimeout`                   | `TimeoutConfig.kvTimeout`
|`viewTimeout`                 | `TimeoutConfig.viewTimeout`
|`searchTimeout`               | `TimeoutConfig.searchTimeout`
|`analyticsTimeout`            | `TimeoutConfig.analyticsTimeout`
|`connectTimeout`              | `TimeoutConfig.connectTimeout`
|`disconnectTimeout`           | `TimeoutConfig.disconnectTimeout`
|`dnsSrvEnabled`               | `IoConfig.enableDnsSrv`
|`cryptoManager`               | removed
|`propagateParentSpan`         | removed
|====
"""
