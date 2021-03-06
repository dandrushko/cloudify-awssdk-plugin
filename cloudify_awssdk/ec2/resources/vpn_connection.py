# #######
# Copyright (c) 2017 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.
"""
    EC2.VPN Connection
    ~~~~~~~~~~~~~~
    AWS EC2 VPN Connection interface
"""
from __future__ import unicode_literals

# Boto
from botocore.exceptions import ClientError


# Cloudify
from cloudify_awssdk.common import decorators, utils
from cloudify_awssdk.ec2 import EC2Base
from cloudify_awssdk.common import constants

RESOURCE_TYPE = 'EC2 VPN Connection'
VPN_CONNECTION_ID = 'VpnConnectionId'
VPN_CONNECTION_IDS = 'VpnConnectionIds'
VPN_CONNECTION = 'VpnConnection'
VPN_CONNECTIONS = 'VpnConnections'


class EC2VPNConnection(EC2Base):
    """
        EC2 VPN Connection interface
    """
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        EC2Base.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE
        self.describe_vpn_connection_filter = {}

    @property
    def properties(self):
        """Gets the properties of an external resource"""
        try:
            resources = \
                self.client.describe_vpn_connections(
                    **self.describe_vpn_connection_filter
                )
        except ClientError:
            pass
        else:
            return None if not resources\
                else resources.get(VPN_CONNECTIONS)[0]

    @property
    def status(self):
        """Gets the status of an external resource"""
        props = self.properties
        if not props:
            return None
        elif props and 'VgwTelemetry' not in props:
            return None
        return props['VgwTelemetry'][0].get('Status')

    def create(self, params):
        """Create a new AWS EC2 VPN Connection."""
        self.logger.debug(
            'Creating {} with parameters: '
            '{}'.format(self.type_name, params)
        )
        res = self.client.create_vpn_connection(**params)
        self.logger.debug('Response: {}'.format(res))
        return res.get(VPN_CONNECTION)

    def delete(self, params=None):
        """ Deletes an existing AWS EC2 VPN Connection."""
        self.client.delete_vpn_connection(**params)


def prepare_describe_vpn_connection_filter(params, iface):
    iface.describe_vpn_connection_filter = {
        VPN_CONNECTION_IDS: [params.get(VPN_CONNECTION_ID)],
    }


@decorators.aws_resource(EC2VPNConnection, resource_type=RESOURCE_TYPE)
def prepare(ctx, resource_config, **_):
    """Prepares an AWS EC2 VPN Connection"""
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(EC2VPNConnection, RESOURCE_TYPE)
def create(ctx, iface, resource_config, **_):
    """Creates an AWS EC2 VPN Connection"""
    params = dict() if not resource_config else resource_config.copy()
    # Actually create the resource
    create_response = iface.create(params)
    ctx.instance.runtime_properties['create_response'] = \
        utils.JsonCleanuper(create_response).to_dict()
    if create_response:
        resource_id = \
            utils.get_resource_id(
                ctx.node,
                ctx.instance,
                create_response.get(VPN_CONNECTION_ID),
                use_instance_id=True
            )

        utils.update_resource_id(ctx.instance, resource_id)
        prepare_describe_vpn_connection_filter(create_response, iface)


@decorators.aws_resource(EC2VPNConnection, RESOURCE_TYPE)
def delete(ctx, iface, resource_config, **_):
    """Deletes an AWS EC2 VPN Connection"""
    deleted_params = dict()
    resource_id = \
        ctx.instance.runtime_properties[constants.EXTERNAL_RESOURCE_ID]
    deleted_params[VPN_CONNECTION_ID] = resource_id

    vpn_connection_config = ctx.instance.runtime_properties['resource_config']
    deleted_params['DryRun'] = vpn_connection_config.get('DryRun') or False
    iface.delete(deleted_params)
