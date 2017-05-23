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
    EC2.Customer Gateway
    ~~~~~~~~~~~~~~
    AWS EC2 Customer Gateway interface
"""
# Cloudify
from cloudify_boto3.common import decorators, utils
from cloudify_boto3.ec2 import EC2Base
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'EC2 Customer Gateway'
CUSTOMERGATEWAYS = 'CustomerGateways'
CUSTOMERGATEWAY_ID = 'CustomerGatewayId'
CUSTOMERGATEWAY_IDS = 'CustomerGatewayIds'
PUBLIC_IP = 'PublicIp'
ELASTICIP_TYPE = 'cloudify.nodes.aws.ec2.ElasticIP'
ELASTICIP_TYPE_DEPRECATED = 'cloudify.aws.nodes.ElasticIP'


class EC2CustomerGateway(EC2Base):
    """
        EC2 Customer Gateway interface
    """
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        EC2Base.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        """Gets the properties of an external resource"""
        params = {CUSTOMERGATEWAY_IDS: [self.resource_id]}
        try:
            resources = \
                self.client.describe_customer_gateways(**params)
        except ClientError:
            pass
        else:
            return resources.get(CUSTOMERGATEWAYS)[0] if resources else None

    @property
    def status(self):
        """Gets the status of an external resource"""
        props = self.properties
        if not props:
            return None
        return props['State']

    def create(self, params):
        """
            Create a new AWS EC2 Customer Gateway.
        """
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_customer_gateway(**params)
        self.logger.debug('Response: %s' % res)
        return res['CustomerGateway']

    def delete(self, params=None):
        """
            Deletes an existing AWS EC2 Customer Gateway.
        """
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.delete_customer_gateway(**params)
        self.logger.debug('Response: %s' % res)
        return res


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def prepare(ctx, resource_config, **_):
    """Prepares an AWS EC2 Customer Gateway"""
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(EC2CustomerGateway, RESOURCE_TYPE)
@decorators.wait_for_status(status_good=['available'],
                            status_pending=['pending'])
def create(ctx, iface, resource_config, **_):
    """Creates an AWS EC2 Customer Gateway"""

    # Create a copy of the resource config for clean manipulation.
    params = \
        dict() if not resource_config else resource_config.copy()

    public_ip = params.get(PUBLIC_IP)
    if not public_ip:
        targ = \
            utils.find_rel_by_node_type(ctx.instance, ELASTICIP_TYPE)
        if targ:
            public_ip = \
                targ.target.instance.runtime_properties \
                    .get(ELASTICIP_TYPE_DEPRECATED)
        params.update({PUBLIC_IP: public_ip})

    # Actually create the resource
    customer_gateway = iface.create(params)
    utils.update_resource_id(ctx.instance,
                             customer_gateway.get(CUSTOMERGATEWAY_ID))


@decorators.aws_resource(EC2CustomerGateway, RESOURCE_TYPE,
                         ignore_properties=True)
@decorators.wait_for_delete(status_deleted=['deleted'],
                            status_pending=['deleting'])
def delete(iface, resource_config, **_):
    """Deletes an AWS EC2 Customer Gateway"""

    # Create a copy of the resource config for clean manipulation.
    params = \
        dict() if not resource_config else resource_config.copy()
    customer_gateway_id = params.get(CUSTOMERGATEWAY_ID)

    if not customer_gateway_id:
        customer_gateway_id = iface.resource_id

    params.update({CUSTOMERGATEWAY_ID: customer_gateway_id})
    iface.delete(params)
