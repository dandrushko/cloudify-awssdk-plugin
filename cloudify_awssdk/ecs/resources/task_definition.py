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
    ECSTaskDefinition
    ~~~~~~~~~~~~~~
    AWS ECS Task Definition interface
"""

from __future__ import unicode_literals

# Boto

from botocore.exceptions import ClientError

# Cloudify
from cloudify_awssdk.common import decorators, utils
from cloudify_awssdk.ecs import ECSBase

RESOURCE_TYPE = 'ECS Task Definition'
TASK_DEFINITION_FAMILY = 'family'
TASK_DEFINITION = 'taskDefinition'
TASK_CONTAINER_DEFINITION = 'containerDefinitions'
TASK_DEFINITION_RESOURCE = 'task_definition'


class ECSTaskDefinition(ECSBase):
    """
        ECSTaskDefinition interface
    """
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        ECSBase.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE
        self.describe_task_definition_filter = {}

    @property
    def properties(self):
        """Gets the properties of an external resource"""
        try:
            resources = \
                self.client.describe_task_definition(
                    **self.describe_task_definition_filter
                )
        except ClientError:
            pass
        else:
            return None if not resources\
                else resources.get(TASK_DEFINITION)

    @property
    def status(self):
        """Gets the status of an external resource"""
        props = self.properties
        if not props:
            return None
        return props.get('status')

    def create(self, params):
        """
            Create a new AWS ECS Task Definition.
        """
        self.logger.debug(
            'Creating {} with parameters: {}'
            ''.format(self.type_name, params)
        )

        res = self.client.register_task_definition(**params)
        self.logger.debug('Response: {}'.format(res))
        return res.get(TASK_DEFINITION)

    def delete(self, params=None):
        """
            Deletes an existing AWS ECS Task Definition.
        """
        self.logger.debug(
            'Deleting {} with parameters: {}'
            ''.format(self.type_name, params)
        )

        res = self.client.deregister_task_definition(**params)
        self.logger.debug('Response: {}'.format(res))
        return res.get(TASK_DEFINITION)


def prepare_describe_task_definition_filter(params, iface):
    iface.describe_task_definition_filter = {
        TASK_DEFINITION: params.get(TASK_DEFINITION_FAMILY),
    }
    return iface


@decorators.aws_resource(resource_type=RESOURCE_TYPE)
def prepare(ctx, resource_config, **_):
    """Prepares an ECS Task Definition"""
    # Save the parameters
    ctx.instance.runtime_properties['resource_config'] = resource_config


@decorators.aws_resource(ECSTaskDefinition, RESOURCE_TYPE)
def create(ctx, iface, resource_config, **_):
    """Creates an AWS ECS Task Definition"""
    params = dict() if not resource_config else resource_config.copy()
    # Get the cluster name from either params or a relationship.
    task_definition_name = params.get(TASK_DEFINITION_FAMILY)

    ctx.instance.runtime_properties[
        TASK_DEFINITION_RESOURCE] = task_definition_name

    utils.update_resource_id(ctx.instance, task_definition_name)
    iface = prepare_describe_task_definition_filter(
        resource_config.copy(), iface
    )
    iface.create(params)


@decorators.aws_resource(ECSTaskDefinition, RESOURCE_TYPE)
def delete(ctx, iface, resource_config, **_):
    """Deletes an AWS ECS Task Definition"""
    task_definition_name = \
        ctx.instance.runtime_properties.get(TASK_DEFINITION_RESOURCE)
    params = {TASK_DEFINITION: task_definition_name}
    iface.delete(params)
