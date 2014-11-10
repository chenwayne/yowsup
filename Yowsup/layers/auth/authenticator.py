from Yowsup.layers import YowLayer, YowLayerEvent, YowProtocolLayer
from Yowsup import ProtocolTreeNode
from .keystream import KeyStream
from Yowsup.common.tools import TimeTools
from .crypt import YowCryptLayer
from .autherror import AuthError
from .protocolentities import *
class YowAuthenticatorLayer(YowProtocolLayer):
    STATE_AUTHED    = 0
    STATE_NOAUTH    = 1

    def __init__(self):
        handleMap = {
            "stream:features": (self.handleStreamFeatures, None),
            "failure": (self.handleFailure, None),
            "success": (self.handleSuccess, None),
            "challenge": (self.handleChallenge, None)
        }
        super(YowAuthenticatorLayer, self).__init__(handleMap)
        self.supportsReceiptAcks = False
        self.state = YowAuthenticatorLayer.STATE_NOAUTH

    def __str__(self):
        return "Autheticator Layer"

    def onEvent(self, event):
        if event.getName() == "network.state.connected":
            self.login()

    ## general methods
    def login(self):
        self._sendFeatures()
        self._sendAuth();

    ###recieved node handlers handlers
    def handleStreamFeatures(self, node):
        nodeEntity = StreamFeaturesProtocolEntity.fromProtocolTreeNode(node)
        self.supportsReceiptAcks  = nodeEntity.supportsReceiptAcks()

    def handleSuccess(self, node):
        self.state = YowAuthenticatorLayer.STATE_AUTHED
        nodeEntity = SuccessProtocolEntity.fromProtocolTreeNode(node)
        self.toUpper(nodeEntity)

    def handleFailure(self, node):
        raise AuthError("Authentication failed")

    def handleChallenge(self, node):
        nodeEntity = ChallengeProtocolEntity.fromProtocolTreeNode(node)
        self._sendResponse(nodeEntity.getNonce())

    ##senders
    def _sendFeatures(self):
        self.entityToLower(StreamFeaturesProtocolEntity())

    def _sendAuth(self):
        self.entityToLower(AuthProtocolEntity(YowAuthenticatorLayer.getProp("credentials")[0]))

    def _sendResponse(self,nonce):
        keys = KeyStream.generateKeys(YowAuthenticatorLayer.getProp("credentials")[1], nonce)

        inputKey = KeyStream(keys[2], keys[3])
        outputKey = KeyStream(keys[0], keys[1])

        YowCryptLayer.setProp("inputKey", inputKey)

        nums = bytearray(4)

        #nums = [0] * 4


        username_bytes = list(map(ord, YowAuthenticatorLayer.getProp("credentials")[0]))
        nums.extend(username_bytes)
        nums.extend(nonce)

        utcNow = str(int(TimeTools.utcTimestamp()))

        time_bytes =  list(map(ord, utcNow))

        nums.extend(time_bytes)

        encoded = outputKey.encodeMessage(nums, 0, 4, len(nums) - 4)
        authBlob = "".join(map(chr, encoded))

        responseEntity = ResponseProtocolEntity(authBlob)
        self.entityToLower(responseEntity)
        YowCryptLayer.setProp("outputKey", outputKey)


