# -*- coding: utf-8 -*-

"""
Copyright (C) 2011 Dariusz Suchojad <dsuch at gefira.pl>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from functools import wraps

# Zato
from zato.common.odb.model import(ChannelAMQP, ChannelWMQ, ChannelZMQ, Cluster, 
    ConnDefAMQP, ConnDefWMQ, CronStyleJob, HTTPBasicAuth, HTTPSOAP, IntervalBasedJob, 
    Job, OutgoingAMQP,  OutgoingFTP, OutgoingS3, OutgoingWMQ, OutgoingZMQ, 
    SecurityBase, Service, SQLConnectionPool, TechnicalAccount, WSSDefinition)

def needs_columns(func):
    """ A decorator for queries which works out whether a given query function
    should return the result only or a column list retrieved in addition
    to the result. This is useful because some callers prefer the former and
    some need the latter.
    """
    @wraps(func)
    def inner(*args):
        # needs_columns is always the last argument so we don't have to look
        # it up using the 'inspect' module or anything like that.
        needs_columns = args[-1]
        
        q = func(*args)
        
        if needs_columns:
            return q.all(), q.statement.columns
        return q.all()
    
    return inner

# ##############################################################################

def internal_channel_list(session, cluster_id):
    """ All the HTTP/SOAP channels that point to internal services.
    """
    return session.query(HTTPSOAP.soap_action, Service.name).\
        filter(HTTPSOAP.cluster_id==Cluster.id).\
        filter(HTTPSOAP.service_id==Service.id).\
        filter(Service.is_internal==True).\
        filter(Cluster.id==cluster_id)

# ##############################################################################

@needs_columns
def job_list(session, cluster_id, needs_columns=False):
    """ All the scheduler's jobs defined in the ODB.
    """
    return session.query(Job.id, Job.name, Job.is_active,
        Job.job_type, Job.start_date,  Job.extra,
        Service.name.label('service_name'), Service.id.label('service_id'),
        IntervalBasedJob.weeks, IntervalBasedJob.days,
        IntervalBasedJob.hours, IntervalBasedJob.minutes,
        IntervalBasedJob.seconds, IntervalBasedJob.repeats,
        CronStyleJob.cron_definition).\
            outerjoin(IntervalBasedJob, Job.id==IntervalBasedJob.job_id).\
            outerjoin(CronStyleJob, Job.id==CronStyleJob.job_id).\
            filter(Cluster.id==cluster_id).\
            filter(Job.service_id==Service.id).\
            order_by('job.name')

# ##############################################################################

@needs_columns
def basic_auth_list(session, cluster_id, needs_columns=False):
    """ All the HTTP Basic Auth definitions.
    """
    return session.query(HTTPBasicAuth.id, HTTPBasicAuth.name,
                         HTTPBasicAuth.is_active, \
                         HTTPBasicAuth.username, HTTPBasicAuth.realm, \
                         HTTPBasicAuth.password, HTTPBasicAuth.sec_type,
                         HTTPBasicAuth.password_type).\
        filter(Cluster.id==cluster_id).\
        order_by('sec_basic_auth.name')

@needs_columns
def tech_acc_list(session, cluster_id, needs_columns=False):
    """ All the technical accounts.
    """
    return session.query(TechnicalAccount.id, TechnicalAccount.name, \
                         TechnicalAccount.is_active, \
                         TechnicalAccount.password, TechnicalAccount.salt, 
                         TechnicalAccount.sec_type, TechnicalAccount.password_type).\
        order_by(TechnicalAccount.name).\
        filter(Cluster.id==cluster_id).\
        order_by('sec_tech_acc.name')

@needs_columns
def wss_list(session, cluster_id, needs_columns=False):
    """ All the WS-Security definitions.
    """
    return session.query(WSSDefinition.id, WSSDefinition.name , WSSDefinition.is_active, \
                         WSSDefinition.username, WSSDefinition.password, WSSDefinition.password_type, \
                         WSSDefinition.reject_empty_nonce_creat, WSSDefinition.reject_stale_tokens, \
                         WSSDefinition.reject_expiry_limit, WSSDefinition.nonce_freshness_time, \
                         WSSDefinition.nonce_freshness_time, WSSDefinition.sec_type).\
        filter(Cluster.id==cluster_id).\
        order_by('sec_wss_def.name')

# ##############################################################################

def _def_amqp(session, cluster_id):
    return session.query(ConnDefAMQP.name, ConnDefAMQP.id, ConnDefAMQP.host,
            ConnDefAMQP.port, ConnDefAMQP.vhost, ConnDefAMQP.username,
            ConnDefAMQP.frame_max, ConnDefAMQP.heartbeat, ConnDefAMQP.password).\
        filter(Cluster.id==ConnDefAMQP.cluster_id).\
        filter(ConnDefAMQP.def_type=='amqp').\
        filter(Cluster.id==cluster_id).\
        order_by(ConnDefAMQP.name)

def def_amqp(session, cluster_id, id):
    """ A particular AMQP definition
    """
    return _def_amqp(session, cluster_id).\
           filter(ConnDefAMQP.id==id).\
           one()


@needs_columns
def def_amqp_list(session, cluster_id, needs_columns=False):
    """ AMQP connection definitions.
    """
    return _def_amqp(session, cluster_id)

# ##############################################################################

def _def_jms_wmq(session, cluster_id):
    return session.query(ConnDefWMQ.id, ConnDefWMQ.name, ConnDefWMQ.host,
            ConnDefWMQ.port, ConnDefWMQ.queue_manager, ConnDefWMQ.channel,
            ConnDefWMQ.cache_open_send_queues, ConnDefWMQ.cache_open_receive_queues,
            ConnDefWMQ.use_shared_connections, ConnDefWMQ.ssl, ConnDefWMQ.ssl_cipher_spec,
            ConnDefWMQ.ssl_key_repository, ConnDefWMQ.needs_mcd, ConnDefWMQ.max_chars_printed).\
        filter(Cluster.id==ConnDefWMQ.cluster_id).\
        filter(Cluster.id==cluster_id).\
        order_by(ConnDefWMQ.name)

def def_jms_wmq(session, cluster_id, id):
    """ A particular JMS WebSphere MQ definition
    """
    return _def_jms_wmq(session, cluster_id).\
           filter(ConnDefWMQ.id==id).\
           one()

@needs_columns
def def_jms_wmq_list(session, cluster_id, needs_columns=False):
    """ JMS WebSphere MQ connection definitions.
    """
    return _def_jms_wmq(session, cluster_id)

# ##############################################################################

def _out_amqp(session, cluster_id):
    return session.query(OutgoingAMQP.id, OutgoingAMQP.name, OutgoingAMQP.is_active,
            OutgoingAMQP.delivery_mode, OutgoingAMQP.priority, OutgoingAMQP.content_type,
            OutgoingAMQP.content_encoding, OutgoingAMQP.expiration, OutgoingAMQP.user_id,
            OutgoingAMQP.app_id, ConnDefAMQP.name.label('def_name'), OutgoingAMQP.def_id).\
        filter(OutgoingAMQP.def_id==ConnDefAMQP.id).\
        filter(ConnDefAMQP.id==OutgoingAMQP.def_id).\
        filter(Cluster.id==ConnDefAMQP.cluster_id).\
        filter(Cluster.id==cluster_id).\
        order_by(OutgoingAMQP.name)

def out_amqp(session, cluster_id, id):
    """ An outgoing AMQP connection.
    """
    return _out_amqp(session, cluster_id).\
           filter(OutgoingAMQP.id==id).\
           one()

@needs_columns
def out_amqp_list(session, cluster_id, needs_columns=False):
    """ Outgoing AMQP connections.
    """
    return _out_amqp(session, cluster_id)

# ##############################################################################

def _out_jms_wmq(session, cluster_id):
    return session.query(OutgoingWMQ.id, OutgoingWMQ.name, OutgoingWMQ.is_active,
            OutgoingWMQ.delivery_mode, OutgoingWMQ.priority, OutgoingWMQ.expiration,
            ConnDefWMQ.name.label('def_name'), OutgoingWMQ.def_id).\
        filter(OutgoingWMQ.def_id==ConnDefWMQ.id).\
        filter(ConnDefWMQ.id==OutgoingWMQ.def_id).\
        filter(Cluster.id==ConnDefWMQ.cluster_id).\
        filter(Cluster.id==cluster_id).\
        order_by(OutgoingWMQ.name)

def out_jms_wmq(session, cluster_id, id):
    """ An outgoing JMS WebSphere MQ connection.
    """
    return _out_jms_wmq(session, cluster_id).\
           filter(OutgoingWMQ.id==id).\
           one()

@needs_columns
def out_jms_wmq_list(session, cluster_id, needs_columns=False):
    """ Outgoing JMS WebSphere MQ connections.
    """
    return _out_jms_wmq(session, cluster_id)

# ##############################################################################

def _channel_amqp(session, cluster_id):
    return session.query(ChannelAMQP.id, ChannelAMQP.name, ChannelAMQP.is_active,
            ChannelAMQP.queue, ChannelAMQP.consumer_tag_prefix,
            ConnDefAMQP.name.label('def_name'), ChannelAMQP.def_id,
            Service.name.label('service_name')).\
        filter(ChannelAMQP.def_id==ConnDefAMQP.id).\
        filter(ChannelAMQP.service_id==Service.id).\
        filter(Cluster.id==ConnDefAMQP.cluster_id).\
        filter(Cluster.id==cluster_id).\
        order_by(ChannelAMQP.name)

def channel_amqp(session, cluster_id, id):
    """ A particular AMQP channel.
    """
    return _channel_amqp(session, cluster_id).\
           filter(ChannelAMQP.id==id).\
           one()

@needs_columns
def channel_amqp_list(session, cluster_id, needs_columns=False):
    """ AMQP channels.
    """
    return _channel_amqp(session, cluster_id)

# ##############################################################################

def _channel_jms_wmq(session, cluster_id):
    return session.query(ChannelWMQ.id, ChannelWMQ.name, ChannelWMQ.is_active,
            ChannelWMQ.queue, ConnDefWMQ.name.label('def_name'), ChannelWMQ.def_id,
            Service.name.label('service_name')).\
        filter(ChannelWMQ.def_id==ConnDefWMQ.id).\
        filter(ChannelWMQ.service_id==Service.id).\
        filter(Cluster.id==ConnDefWMQ.cluster_id).\
        filter(Cluster.id==cluster_id).\
        order_by(ChannelWMQ.name)

def channel_jms_wmq(session, cluster_id, id):
    """ A particular JMS WebSphere MQ channel.
    """
    return _channel_jms_wmq(session, cluster_id).\
           filter(ChannelWMQ.id==id).\
           one()

@needs_columns
def channel_jms_wmq_list(session, cluster_id, needs_columns=False):
    """ JMS WebSphere MQ channels.
    """
    return _channel_jms_wmq(session, cluster_id)

# ##############################################################################

def _out_zmq(session, cluster_id):
    return session.query(OutgoingZMQ.id, OutgoingZMQ.name, OutgoingZMQ.is_active,
            OutgoingZMQ.address, OutgoingZMQ.socket_type).\
        filter(Cluster.id==OutgoingZMQ.cluster_id).\
        filter(Cluster.id==cluster_id).\
        order_by(OutgoingZMQ.name)

def out_zmq(session, cluster_id, id):
    """ An outgoing ZeroMQ connection.
    """
    return _out_zmq(session, cluster_id).\
           filter(OutgoingZMQ.id==id).\
           one()

@needs_columns
def out_zmq_list(session, cluster_id, needs_columns=False):
    """ Outgoing ZeroMQ connections.
    """
    return _out_zmq(session, cluster_id)

# ##############################################################################

def _channel_zmq(session, cluster_id):
    return session.query(ChannelZMQ.id, ChannelZMQ.name, ChannelZMQ.is_active,
            ChannelZMQ.address, ChannelZMQ.socket_type, ChannelZMQ.sub_key, 
            Service.name.label('service_name')).\
        filter(Cluster.id==ChannelZMQ.cluster_id).\
        filter(Service.id==ChannelZMQ.service_id).\
        filter(Cluster.id==cluster_id).\
        order_by(ChannelZMQ.name)

def channel_zmq(session, cluster_id, id):
    """ An incoming ZeroMQ connection.
    """
    return _channel_zmq(session, cluster_id).\
           filter(ChannelZMQ.id==id).\
           one()

@needs_columns
def channel_zmq_list(session, cluster_id, needs_columns=False):
    """ Incoming ZeroMQ connections.
    """
    return _channel_zmq(session, cluster_id)

# ##############################################################################

def _http_soap(session, cluster_id):
    return session.query(HTTPSOAP.id, HTTPSOAP.name, HTTPSOAP.is_active, 
            HTTPSOAP.is_internal, HTTPSOAP.transport, HTTPSOAP.host, 
            HTTPSOAP.url_path, HTTPSOAP.method, HTTPSOAP.soap_action, 
            HTTPSOAP.soap_version, HTTPSOAP.security_id,
            SecurityBase.sec_type,
            Service.name.label('service_name'),
            Service.id.label('service_id'),
            Service.impl_name,
            SecurityBase.name.label('security_name'),
            SecurityBase.username.label('username'),
            SecurityBase.password.label('password'),
            SecurityBase.password_type.label('password_type'),
            ).\
           outerjoin(Service, Service.id==HTTPSOAP.service_id).\
           outerjoin(SecurityBase, HTTPSOAP.security_id==SecurityBase.id).\
           order_by(HTTPSOAP.name)

# No point in creating a new function if we can alias an already existing one.
http_soap_security_list = _http_soap

def http_soap(session, cluster_id, id):
    """ An HTTP/SOAP connection.
    """
    return _http_soap(session, cluster_id).\
           filter(HTTPSOAP.id==id).\
           one()

@needs_columns
def http_soap_list(session, cluster_id, connection=None, transport=None, needs_columns=False):
    """ HTTP/SOAP connections, both channels and outgoing ones.
    """
    q = _http_soap(session, cluster_id)
    
    if connection:
        q = q.filter(HTTPSOAP.connection==connection)
        
    if transport:
        q = q.filter(HTTPSOAP.transport==transport)
        
    return q

# ##############################################################################

def _out_s3(session, cluster_id):
    return session.query(OutgoingS3.id, OutgoingS3.name, OutgoingS3.is_active,
            OutgoingS3.prefix, OutgoingS3.separator,
            OutgoingS3.key_sync_timeout).\
        filter(Cluster.id==OutgoingS3.cluster_id).\
        filter(Cluster.id==cluster_id).\
        order_by(OutgoingS3.name)

def out_s3(session, cluster_id, id):
    """ An outgoing S3 connection.
    """
    return _out_s3(session, cluster_id).\
           filter(OutgoingS3.id==id).\
           one()

@needs_columns
def out_s3_list(session, cluster_id, needs_columns=False):
    """ Outgoing S3 connections.
    """
    return _out_s3(session, cluster_id)

# ##############################################################################

def _out_sql(session, cluster_id):
    return session.query(SQLConnectionPool).\
        filter(Cluster.id==SQLConnectionPool.cluster_id).\
        filter(Cluster.id==cluster_id).\
        order_by(SQLConnectionPool.name)

def out_sql(session, cluster_id, id):
    """ An outgoing SQL connection.
    """
    return _out_sql(session, cluster_id).\
           filter(SQLConnectionPool.id==id).\
           one()

@needs_columns
def out_sql_list(session, cluster_id, needs_columns=False):
    """ Outgoing SQL connections.
    """
    return _out_sql(session, cluster_id)

# ##############################################################################

def _out_ftp(session, cluster_id):
    return session.query(OutgoingFTP.id, OutgoingFTP.name, OutgoingFTP.is_active,
            OutgoingFTP.host, OutgoingFTP.port, OutgoingFTP.user, OutgoingFTP.password,  
            OutgoingFTP.acct, OutgoingFTP.timeout, OutgoingFTP.dircache).\
        filter(Cluster.id==OutgoingFTP.cluster_id).\
        filter(Cluster.id==cluster_id).\
        order_by(OutgoingFTP.name)

def out_ftp(session, cluster_id, id):
    """ An outgoing FTP connection.
    """
    return _out_ftp(session, cluster_id).\
           filter(OutgoingFTP.id==id).\
           one()

@needs_columns
def out_ftp_list(session, cluster_id, needs_columns=False):
    """ Outgoing FTP connections.
    """
    return _out_ftp(session, cluster_id)

# ##############################################################################

def _service(session, cluster_id):
    return session.query(Service.id, Service.name, Service.is_active,
            Service.impl_name, Service.is_internal).\
        filter(Cluster.id==Service.cluster_id).\
        filter(Cluster.id==cluster_id).\
        order_by(Service.name)

def service(session, cluster_id, id):
    """ A service.
    """
    return _service(session, cluster_id).\
           filter(Service.id==id).\
           one()

@needs_columns
def service_list(session, cluster_id, needs_columns=False):
    """ All services.
    """
    return _service(session, cluster_id)

# ##############################################################################
