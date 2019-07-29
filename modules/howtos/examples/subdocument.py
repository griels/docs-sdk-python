import couchbase.subdocument as SD
from couchbase.cluster import Cluster, ClusterOptions
from couchbase_core.cluster import PasswordAuthenticator

config = None
cluster = Cluster("127.0.0.1",
                  ClusterOptions(PasswordAuthenticator("Administrator","password")))
bucket = cluster.bucket("default")
_collection = bucket.default_collection()


def get(self):
    # #tag::get[]
    result = _collection.lookup_in("customer123", SD.get("addresses.delivery.country"))

    country = result.content_as[str](0)  # type: str
    # #end::get[]


def exists(self):
    # #tag::exists[]
    result = _collection.lookup_in("customer123",
        SD.exists("addresses.delivery.does_not_exist")
    )

    exists = result.content_as[bool](0) # type: bool
    # #end::exists[]


def combine(self):
    # #tag::combine[]
    result = _collection.lookup_in("customer123",
                                   (SD.get("addresses.delivery.country"),
                                    SD.exists("addresses.delivery.does_not_exist")))

    country = result.content_as[str](0)  # type: str
    exists = result.content_as[bool](1)  # type: bool
    # #end::combine[]


def upsert(self):
    # #tag::upsert[]
    _collection.mutate_in("customer123",
        SD.upsert("email", "dougr96@hotmail.com")
    )
    # #end::upsert[]


def insert(self):
    # #tag::insert[]
    _collection.mutate_in("customer123",
        SD.insert("email", "dougr96@hotmail.com")
    )
    # #end::insert[]


def multi(self):
    # #tag::multi[]
    _collection.mutate_in("customer123",
        SD.remove("addresses.billing"),
        SD.replace("email", "dougr96@hotmail.com"))
    # #end::multi[]


def array_append(self):
    # #tag::array-append[]
    _collection.mutate_in("customer123",
        SD.array_append("purchases.complete", 777)
    )
    # purchases.complete is now [339, 976, 442, 666, 777]
    # #end::array-append[]


def array_prepend(self):
    # #tag::array-prepend[]
    _collection.mutate_in("customer123",
        SD.array_prepend("purchases.abandoned", 18))

    # purchases.abandoned is now [18, 157, 49, 999]
    # #end::array-prepend[]


def create_and_populate_arrays(self):
    # #tag::array-create[]
    _collection.Upsert("my_array", [])

    _collection.mutate_in("my_array",
        SD.array_append("", "some element")
    )
    # the document my_array is now ["some element"]
    # #end::array-create[]


def array_create(self):
    # #tag::array-upsert[]
    _collection.mutate_in("some_doc",
        SD.array_append("some.array", "hello world", create_parents=True))
    # #end::array-upsert[]


def array_unique(self):
    # #tag::array-unique[]
    _collection.mutate_in("customer123",
        SD.array_addunique("purchases.complete", 95)
    )
    # #end::array-unique[]


def array_insert(self):
    # #tag::array-insert[]
    _collection.mutate_in("some_doc",
        SD.array_insert("foo.bar[1]", "cruel")
    )
    # #end::array-insert[]


def counter_inc(self):
    # #tag::counter-inc[]
    result = _collection.mutate_in("customer123",
        SD.counter("logins", 1)
    )

    # Counter operations return the updated count
    count = result.content_as[float][0]
    # #end::counter-inc[]


def counter_dec(self):
    # #tag::counter-dec[]
    _collection.upsert("player432", {'gold':1000})

    result = _collection.mutate_in("player432",
        SD.counter("gold", -150)
    )

    count = result.content_as[float][0]
    # #end::counter-dec[]


def create_path(self):
    # #tag::create-path[]
    _collection.mutate_in("customer123",
        SD.upsert("level_0.level_1.foo.bar.phone",{'num':"311-555-0101", 'ext':16 }, create_parents=True))
    # #end::create-path[]


def cas(self):
    # #tag::cas[]
    player = _collection.Get("player432")
    _collection.mutate_in("player432", SD.counter("gold", -150),
       cas=player.cas
    )
    # #end::cas[]

