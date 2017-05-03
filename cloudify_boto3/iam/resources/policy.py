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
'''
    IAM.Policy
    ~~~~~~~~~~
    AWS IAM Policy interface
'''
from json import dumps as json_dumps
# Cloudify
from cloudify_boto3.common import decorators, utils
from cloudify_boto3.iam import IAMBase
# Boto
from botocore.exceptions import ClientError

RESOURCE_TYPE = 'IAM Policy'


class IAMPolicy(IAMBase):
    '''
        AWS IAM Policy interface
    '''
    def __init__(self, ctx_node, resource_id=None, client=None, logger=None):
        IAMBase.__init__(self, ctx_node, resource_id, client, logger)
        self.type_name = RESOURCE_TYPE

    @property
    def properties(self):
        '''Gets the properties of an external resource'''
        resource = None
        try:
            resource = self.client.get_policy(PolicyArn=self.resource_id)
        except ClientError:
            pass
        if not resource or not resource.get('Policy', dict()):
            return None
        return resource['Policy']

    @property
    def status(self):
        '''Gets the status of an external resource'''
        if self.properties:
            return 'available'
        return None

    def create(self, params):
        '''
            Create a new AWS IAM Policy.
        '''
        self.logger.debug('Creating %s with parameters: %s'
                          % (self.type_name, params))
        res = self.client.create_policy(**params)
        self.logger.debug('Response: %s' % res)
        self.update_resource_id(res['Policy']['Arn'])
        return res['Policy']['PolicyName'], res['Policy']['Arn']

    def delete(self, params=None):
        '''
            Deletes an existing AWS IAM Policy.
        '''
        params = params or dict()
        params.update(dict(PolicyArn=self.resource_id))
        self.logger.debug('Deleting %s with parameters: %s'
                          % (self.type_name, params))
        self.client.delete_policy(**params)


@decorators.aws_resource(IAMPolicy, RESOURCE_TYPE)
def create(ctx, iface, resource_config, **_):
    '''Creates an AWS IAM Policy'''
    # Build API params
    params = resource_config
    params.update(dict(PolicyName=iface.resource_id))
    if 'PolicyDocument' in params and \
            isinstance(params['PolicyDocument'], dict):
        params['PolicyDocument'] = json_dumps(params['PolicyDocument'])
    # Actually create the resource
    res_id, res_arn = iface.create(params)
    utils.update_resource_id(ctx.instance, res_id)
    utils.update_resource_arn(ctx.instance, res_arn)


@decorators.aws_resource(IAMPolicy, RESOURCE_TYPE,
                         ignore_properties=True)
@decorators.wait_for_delete()
def delete(iface, resource_config, **_):
    '''Deletes an AWS IAM Policy'''
    iface.update_resource_id(utils.get_resource_arn())
    iface.delete(resource_config)