
require( "unclasslib" )
require( "qt.object" )

CIceServer = class( CObject )

function CIceServer:__init()
    self[CObject]:__init( "CIceServer" )
end


function CIceServer:setProperty( prop, val )
    callMethodDirect( self:object(), "setProperty", prop, val )
end

function CIceServer:setAdapter( name, identity, params )
    callMethodDirect( self:object(), "setAdapter", name, identity, params )
end

function CIceServer:start()
    callMethodDirect( self:object(), "start" )
end

function CIceServer:destroy()
    callMethodDirect( self:object(), "destroy" )
end

function CIceServer:errorsCnt()
    local res = callMethodDirect( self:object(), "errorsCnt" )
    return res
end

function CIceServer:error()
    local res = callMethodDirect( self:object(), "error" )
    return res
end

function CIceServer:isIdle()
    local res = callMethodDirect( self:object(), "isIdle" )
    return res
end

function CIceServer:isConnecting()
    local res = callMethodDirect( self:object(), "isConnecting" )
    return res
end

function CIceServer:isConnected()
    local res = callMethodDirect( self:object(), "isConnected" )
    return res
end

function CIceServer:isDisconnected()
    local res = callMethodDirect( self:object(), "isDisconnected" )
    return res
end









CIceClient = class( CObject )

function CIceClient:__init()
    self[CObject]:__init( "CIceClient" )
end

function CIceClient:setProperty( prop, val )
    callMethodDirect( self:object(), "setProperty", prop, val )
end

function CIceClient:setServer( server )
    callMethodDirect( self:object(), "setServer", server )
end

function CIceClient:start()
    callMethodDirect( self:object(), "start" )
end

function CIceClient:destroy()
    callMethodDirect( self:object(), "destroy" )
end

function CIceClient:errorsCnt()
    local res = callMethodDirect( self:object(), "errorsCnt" )
    return res
end

function CIceClient:error()
    local res = callMethodDirect( self:object(), "error" )
    return res
end

function CIceClient:callSlot( slot, ... )
    callMethodDirect( self:object(), "callSlot", slot, ... )
end

function CIceClient:callSlotOne( index, slot, ... )
    callMethodDirect( self:object(), "callSlotOne", index, slot, ... )
end

function CIceClient:callSlotAll( slot, ... )
    callMethodDirect( self:object(), "callSlotAll", slot, ... )
end

-- обязательно что-нить послать!
function CIceClient:sendArgs( slot, ... )
    callMethodDirect( self:object(), "callSlotAll", "sendArgs", slot, ... )
end

function CIceClient:clientsUpdate()
    callMethodDirect( self:object(), "clientsUpdate" )
end

function CIceClient:clientsUpdated()
    local res = callMethodDirect( self:object(), "clientsUpdated" )
    return res
end

function CIceClient:clientsCnt()
    local res = callMethodDirect( self:object(), "clientsCnt" )
    return res
end

function CIceClient:clients()
    return callMethodDirect( self:object(), "clients" )
end

function CIceClient:clientValid( index )
    local res = callMethodAsynch( self:object(), "clientValid", index )
    return res
end

function CIceClient:selfIndex()
    local res = callMethodAsynch( self:object(), "selfIndex" )
    return res
end

function CIceClient:isIdle()
    local res = callMethodDirect( self:object(), "isIdle" )
    return res
end

function CIceClient:isConnecting()
    local res = callMethodDirect( self:object(), "isConnecting" )
    return res
end

function CIceClient:isConnected()
    local res = callMethodDirect( self:object(), "isConnected" )
    return res
end

function CIceClient:isDisconnected()
    local res = callMethodDirect( self:object(), "isDisconnected" )
    return res
end

function CIceClient:getArgs( slot )
    local args = { callMethodDirect( self:object(), "getArgs", slot ) }
    if #args < 1 then
        return nil
    end
    return args
end






