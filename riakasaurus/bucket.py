"""
Copyright 2010 Rusty Klophaus <rusty@basho.com>
Copyright 2010 Justin Sheehy <justin@basho.com>
Copyright 2009 Jay Baird <jay@mochimedia.com>

This file is provided to you under the Apache License,
Version 2.0 (the "License"); you may not use this file
except in compliance with the License.  You may obtain
a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
"""
from twisted.internet import defer

from riakasaurus.riak_object import RiakObject
from twisted.python import log
from twisted.internet import defer,reactor

import mimetypes

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

class RiakBucket(object):
    """
    The ``RiakBucket`` object allows you to access and change information
    about a Riak bucket, and provides methods to create or retrieve
    objects within the bucket.
    """

    def __init__(self, client, name,bucket_type = 'default'):
        """
        Returns a new ``RiakBucket`` instance.

        :param client: A :class:`RiakClient <riak.client.RiakClient>` instance
        :type client: :class:`RiakClient <riak.client.RiakClient>`
        :param name: The bucket name
        :type name: string
        """
        try:
            if isinstance(name, basestring):
                name = name.encode('ascii')
            if isinstance(bucket_type, basestring):
                bucket_type = bucket_type.encode('ascii')
        except UnicodeError:
            raise TypeError('Unicode bucket names are not supported.')

        self._client = client
        self._name = name
        self._bucket_type = bucket_type
        self._r = None
        self._w = None
        self._dw = None
        self._rw = None
        self._pr = None
        self._pw = None
        self._encoders = {}
        self._decoders = {}

    def get_name(self):
        """
        Get the bucket name as a string.
        """
        return self._name
    @property
    def bucket_type(self):
        return self._bucket_type

    @property
    def name(self):
        return self._name

    def get_r(self, r=None):
        """
        Get the R-value for this bucket, if it is set, otherwise return
        the R-value for the client.

        :rtype: integer
        """
        if (r is not None):
            return r
        if (self._r is not None):
            return self._r
        return self._client.get_r()

    def set_r(self, r):
        """
        Set the R-value for this bucket. This value is used by :func:`get`
        and :func:`get_binary` operations that do not specify an R-value.

        :param r: The new R-value.
        :type r: integer
        :rtype: self
        """
        self._r = r
        return self

    def get_w(self, w=None):
        """
        Get the W-value for this bucket, if it is set, otherwise return
        the W-value for the client.

        :rtype: integer
        """
        if (w is not None):
            return w
        if (self._w is not None):
            return self._w
        return self._client.get_w()

    def set_w(self, w):
        """
        Set the W-value for this bucket. See :func:`set_r` for
        more information.

        :param w: The new W-value.
        :type w: integer
        :rtype: self
        """
        self._w = w
        return self

    def get_dw(self, dw=None):
        """
        Get the DW-value for this bucket, if it is set, otherwise return
        the DW-value for the client.

        :rtype: integer
        """
        if (dw is not None):
            return dw
        if (self._dw is not None):
            return self._dw
        return self._client.get_dw()

    def set_dw(self, dw):
        """
        Set the DW-value for this bucket. See :func:`set_r` for more
        information.

        :param dw: The new DW-value
        :type dw: integer
        :rtype: self
        """
        self._dw = dw
        return self

    def get_rw(self, rw=None):
        """
        Get the RW-value for this bucket, if it is set, otherwise return
        the RW-value for the client.

        :rtype: integer
        """
        if (rw is not None):
            return rw
        if (self._rw is not None):
            return self._rw
        return self._client.get_rw()

    def set_rw(self, rw):
        """
        Set the RW-value for this bucket. See :func:`set_r` for more
        information.

        :param rw: The new RW-value
        :type rw: integer
        :rtype: self
        """
        self._rw = rw
        return self

    def get_pr(self, pr=None):
        """
        Get the PR-value for this bucket, if it is set, otherwise return
        the PR-value for the client.

        :rtype: integer
        """
        if (pr is not None):
            return pr
        if (self._pr is not None):
            return self._pr
        return self._client.get_pr()

    def set_pr(self, pr):
        """
        Set the PR-value for this bucket. See :func:`set_r` for more
        information.

        :param pr: The new PR-value
        :type pr: integer
        :rtype: self
        """
        self._pr = pr
        return self

    def get_pw(self, pw=None):
        """
        Get the PW-value for this bucket, if it is set, otherwise return
        the PW-value for the client.

        :rtype: integer
        """
        if (pw is not None):
            return pw
        if (self._pw is not None):
            return self._pw
        return self._client.get_pw()

    def set_pw(self, pw):
        """
        Set the PW-value for this bucket. See :func:`set_r` for more
        information.

        :param pw: The new PR-value
        :type pw: integer
        :rtype: self
        """
        self._pw = pw
        return self

    def get_encoder(self, content_type):
        """
        Get the encoding function for the provided content type for this
        bucket.

        :param content_type: Content type requested
        """
        if content_type in self._encoders:
            return self._encoders[content_type]
        else:
            return self._client.get_encoder(content_type)

    def set_encoder(self, content_type, encoder):
        """
        Set the encoding function for the provided content type for this
        bucket.

        :param content_type: Content type for encoder
        :param encoder: Function to encode with - will be called with data as
                        single argument.
        """
        self._encoders[content_type] = encoder
        return self

    def get_decoder(self, content_type):
        """
        Get the decoding function for the provided content type for this
        bucket.

        :param content_type: Content type for decoder
        """
        if content_type in self._decoders:
            return self._decoders[content_type]
        else:
            return self._client.get_decoder(content_type)

    def set_decoder(self, content_type, decoder):
        """
        Set the decoding function for the provided content type for this
        bucket.

        :param content_type: Content type for decoder
        :param decoder: Function to decode with - will be called with string
        """
        self._decoders[content_type] = decoder
        return self

    def new(self, key=None, data=None, content_type='application/json'):
        """
        Create a new :class:`RiakObject <riak.riak_object.RiakObject>` that
        will be stored as JSON. A shortcut for manually instantiating a
        :class:`RiakObject <riak.riak_object.RiakObject>`.

        :param key: Name of the key. Leaving this to be None (default) will
                    make Riak generate the key on store.
        :type key: string
        :param data: The data to store.
        :type data: object
        :rtype: :class:`RiakObject <riak.riak_object.RiakObject>`
        """
        try:
            if isinstance(data, basestring):
                data = data.encode('ascii')
        except UnicodeError:
            raise TypeError('Unicode data values are not supported.')

        obj = RiakObject(self._client, self, key)
        obj.set_data(data)
        obj.set_content_type(content_type)
        obj._encode_data = True
        return obj

    def new_binary(self, key, data, content_type='application/octet-stream'):
        """
        Create a new :class:`RiakObject <riak.riak_object.RiakObject>` that
        will be stored as plain text/binary.
        A shortcut for manually instantiating a
        :class:`RiakObject <riak.riak_object.RiakObject>`.

        :param key: Name of the key.
        :type key: string
        :param data: The data to store.
        :type data: object
        :param content_type: The content type of the object.
        :type content_type: string
        :rtype: :class:`RiakObject <riak.riak_object.RiakObject>`
        """
        obj = RiakObject(self._client, self, key)
        obj.set_data(data)
        obj.set_content_type(content_type)
        obj._encode_data = False
        return obj

    def get(self, key, r=None, pr=None):
        """
        Retrieve a JSON-encoded object from Riak.

        :param key: Name of the key.
        :type key: string
        :param r: R-Value of the request (defaults to bucket's R)
        :type r: integer
        :param pr: PR-Value of the request (defaults to bucket's PR)
        :type pr: integer
        :rtype: :class:`RiakObject <riak.riak_object.RiakObject>`
        """
        obj = RiakObject(self._client, self, key)
        obj._encode_data = True
        r = self.get_r(r)
        pr = self.get_pr(pr)
        return obj.reload(r=r, pr=pr)

    def delete(self, key, **kwargs):
        """Deletes an object from riak. Short hand for
        bucket.new(key).delete(). See :meth:`RiakClient.delete()
        <riak.client.RiakClient.delete>` for options.

        :param key: The key for the object
        :type key: string
        :rtype: RiakObject
        """
        return self.new(key).delete(**kwargs)


    def head(self, key, r=None, pr=None):
        """
        Retrieve a JSON-encoded object from Riak.

        :param key: Name of the key.
        :type key: string
        :param r: R-Value of the request (defaults to bucket's R)
        :type r: integer
        :param pr: PR-Value of the request (defaults to bucket's PR)
        :type pr: integer
        :rtype: :class:`RiakObject <riak.riak_object.RiakObject>`
        """
        obj = RiakObject(self._client, self, key)
        obj._encode_data = True
        r = self.get_r(r)
        pr = self.get_pr(pr)
        return obj.head(r=r, pr=pr)

    def get_binary(self, key, r=None, pr=None):
        """
        Retrieve a binary/string object from Riak.

        :param key: Name of the key.
        :type key: string
        :param r: R-Value of the request (defaults to bucket's R)
        :type r: integer
        :param pr: PR-Value of the request (defaults to bucket's PR)
        :type pr: integer
        :rtype: :class:`RiakObject <riak.riak_object.RiakObject>`
        """
        obj = RiakObject(self._client, self, key)
        obj._encode_data = False
        r = self.get_r(r)
        pr = self.get_pr(pr)
        return obj.reload(r=r, pr=pr)

    def set_n_val(self, nval):
        """
        Set the N-value for this bucket, which is the number of replicas
        that will be written of each object in the bucket.

        .. warning::

           Set this once before you write any data to the bucket, and never
           change it again, otherwise unpredictable things could happen.
           This should only be used if you know what you are doing.

        :param nval: The new N-Val.
        :type nval: integer
        """
        return self.set_property('n_val', nval)

    @defer.inlineCallbacks
    def set_search_index(self,index,max_retry = 10):
        try:
            yield self.set_property('search_index',index)
        except:
            log.msg('Error set search index %s for %s ,retrying' %(index,self.name))
            if max_retry > 0:
                d = defer.Deferred()
                d.addCallback(self.set_search_index,max_retry-1)
                reactor.callLater(2,d.callback,index)
                res = yield d
                defer.returnValue(res)

    @defer.inlineCallbacks
    def get_search_index(self):
        index = yield self.get_property('search_index')
        defer.returnValue(index)

    def get_n_val(self):
        """
        Retrieve the N-value for this bucket.

        :rtype: integer
        """
        return self.get_property('n_val')

    def set_default_r_val(self, rval):
        return self.set_property('r', rval)

    def get_default_r_val(self):
        return self.get_property('r')

    def set_default_w_val(self, wval):
        return self.set_property('w', wval)

    def get_default_w_val(self):
        return self.get_property('w')

    def set_default_dw_val(self, dwval):
        return self.set_property('dw', dwval)

    def get_default_dw_val(self):
        return self.get_property('dw')

    def set_default_rw_val(self, rwval):
        return self.set_property('rw', rwval)

    def get_default_rw_val(self):
        return self.get_property('rw')

    def set_allow_multiples(self, bool):
        """
        If set to True, then writes with conflicting data will be stored
        and returned to the client. This situation can be detected by
        calling has_siblings() and get_siblings().

        .. warning::

           This should only be used if you know what you are doing, as it can
           lead to unexpected results.

        :param bool: True to store and return conflicting writes.
        :type bool: boolean
        """
        return self.set_property('allow_mult', bool)

    def get_allow_multiples(self):
        """
        Retrieve the 'allow multiples' setting.

        :rtype: Boolean
        """
        return self.get_bool_property('allow_mult')

    def set_property(self, key, value):
        """
        Set a bucket property.

        .. warning::

           This should only be used if you know what you are doing.

        :param key: Property to set.
        :type key: string
        :param value: Property value.
        :type value: mixed
        """
        return self.set_properties({key: value})

    @defer.inlineCallbacks
    def get_bool_property(self, key):
        """
        Get a boolean bucket property.  Converts to a ``True`` or ``False``
        value.

        :param key: Property to set.
        :type key: string
        """
        prop = yield self.get_property(key)
        if prop == True or prop > 0:
            defer.returnValue(True)
        else:
            defer.returnValue(False)

    @defer.inlineCallbacks
    def get_property(self, key):
        """
        Retrieve a bucket property.

        :param key: The property to retrieve.
        :type key: string
        :rtype: mixed
        """
        props = yield self.get_properties()
        if (key in props.keys()):
            defer.returnValue(props[key])
        else:
            defer.returnValue(None)

    def set_properties(self, props):
        """
        Set multiple bucket properties in one call.

        .. warning::

           This should only be used if you know what you are doing.

        :param props: An associative array of key:value.
        :type props: array - deferred
        """
        return self._client.transport.set_bucket_props(self, props)

    def get_properties(self):
        """
        Retrieve an associative array of all bucket properties.

        :rtype: array - deferred
        """
        return self._client.transport.get_bucket_props(self)

    def reset_properties(self):
        """
        Reset all bucket properties to defaults.

        :rtype: None - deferred
        """
        return self._client.transport.reset_bucket_props(self)

    def get_keys(self):
        """
        Return all keys within the bucket.

        .. warning::

           At current, this is a very expensive operation. Use with caution.
        """
        return self._client.transport.get_keys(self)

    def new_binary_from_file(self, key, filename):
        """
        Create a new Riak object in the bucket, using the content of the
        specified file.
        """
        binary_data = open(filename, "rb").read()
        mimetype, encoding = mimetypes.guess_type(filename)
        if not mimetype:
            mimetype = 'application/octet-stream'
        return self.new_binary(key, binary_data, mimetype)

    @defer.inlineCallbacks
    def search_enabled(self):
        """
        Returns True if the search precommit hook is enabled for this bucket.
        """
        pch = yield self.get_property("search")
        defer.returnValue(pch)

    @defer.inlineCallbacks
    def enable_search(self,index_name = '',schema = ''):
        """
        Enable search for this bucket by installing the precommit hook to
        index objects in it.
        Returns deferred
        default index will use the bucket name as index
        default schema will use the default schema(dynamic) as index
        """
        current_index = yield self.get_search_index()
        index_name = self.name if not index_name else index_name
        current_index = yield self._client.get_search_index(index_name)
        if not current_index:
            if not schema:
                yield self._client.create_search_index(index_name)
            else:
                yield self._client.create_search_index(index_name,schema)
        if current_index != index_name:
            yield self.set_search_index(index_name)
        defer.returnValue(True)

    @defer.inlineCallbacks
    def search(self, query, **params):
        """
        Queries a search index over objects in this bucket/index.
        """
        index = yield self.get_search_index()
        if index:
            res = yield self._client.solr().search(index, query, **params)
            defer.returnValue(res)
        else:
            raise Exception("Current %s bucket haven't bind to a search index yet" %self.name)

    def get_index(self, index, startkey, endkey=None, return_terms=None,
                  max_results=None,continuation=None):
        """
        Queries a secondary index over objects in this bucket, returning keys.
        """
        return self._client.transport.get_index(
            self._name,index, startkey, endkey,return_terms=return_terms,max_results=max_results,continuation=continuation,bucket_type = self.bucket_type)

    def list_keys(self):
        """ Same as get_keys - for txRiak compat """
        return self.get_keys()

    @defer.inlineCallbacks
    def purge_keys(self,enable_parallel=False,parallel=5):
        """
        Purge all keys from the bucket. Specific to Riakasaurus

        :returns: None

        This is a convenience function that lists all of the keys
        in the bucket and then deletes them.

        NB: This is a VERY resource-intensive operation, and is
            IRREVERSIBLE. Be careful.
        """

        # Get the current key list
        keys = yield self.get_keys()
        # Major key-killing action
        if enable_parallel:
            for l in chunks(keys,parallel):
                dl = defer.DeferredList(map(lambda x:self.get_binary(x).addCallbacks(lambda obj:obj.delete(),log.err),l))
                yield dl
        else:
            for key in keys:
                obj = yield self.get_binary(key)
                yield obj.delete()
        yield self.reset_properties()

    @defer.inlineCallbacks
    def fetch_datatype(self,key,r=None, pr=None,
                       basic_quorum=None, notfound_ok=None, timeout=None,
                       include_context=None):
        """
        fetch_datatype(key, r=None, pr=None, basic_quorum=None,
                       notfound_ok=None, timeout=None, include_context=None)

        Fetches the value of a Riak Datatype.

        .. note:: This request is automatically retried :attr:`retries`
           times if it fails due to network error.

        :param key: the key of the datatype
        :type key: string
        :param r: the read quorum
        :type r: integer, string, None
        :param pr: the primary read quorum
        :type pr: integer, string, None
        :param basic_quorum: whether to use the "basic quorum" policy
           for not-founds
        :type basic_quorum: bool
        :param notfound_ok: whether to treat not-found responses as successful
        :type notfound_ok: bool
        :param timeout: a timeout value in milliseconds
        :type timeout: int
        :param include_context: whether to return the opaque context
          as well as the value, which is useful for removal operations
          on sets and maps
        :type include_context: bool
        :rtype: a subclass of :class:`~riak.datatypes.Datatype`
        """
        res = yield self._client.transport.fetch_datatype(self,key,r=r, pr=pr,
                                          basic_quorum=basic_quorum,
                                          notfound_ok=notfound_ok,
                                          timeout=timeout,
                                          include_context=include_context)
        defer.returnValue(res)

    @defer.inlineCallbacks
    def update_datatype(self, datatype, w=None, dw=None,
                        pw=None, return_body=None, timeout=None,
                        include_context=None):
        """
        Updates a Riak Datatype. This operation is not idempotent and
        so will not be retried automatically.

        :param datatype: the datatype to update
        :type datatype: a subclass of :class:`~riak.datatypes.Datatype`
        :param w: the write quorum
        :type w: integer, string, None
        :param dw: the durable write quorum
        :type dw: integer, string, None
        :param pw: the primary write quorum
        :type pw: integer, string, None
        :param timeout: a timeout value in milliseconds
        :type timeout: int
        :param include_context: whether to return the opaque context
          as well as the value, which is useful for removal operations
          on sets and maps
        :type include_context: bool
        :rtype: a subclass of :class:`~riak.datatypes.Datatype`, bool
        """
        res = yield self._client.transport.update_datatype(datatype, w=w,
                                           dw=dw, pw=pw,
                                           return_body=return_body,
                                           timeout=timeout,
                                           include_context=include_context)
                #defer.returnValue( TYPES[result[0]](result[1], result[2]) )
        defer.returnValue(res)

