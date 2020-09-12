local hmac = require "openssl.hmac"
local base64 = require "base64"


local function tohex(b)
    local x = ""
    for i=1, #b do
        x = x .. string.format("%.2x", string.byte(b,i))
    end
    return x
end

local function extractkv(token)
    local j = 0
    for t in string.gmatch(token, "[^:]+") do
        j = j + 1
        if j == 2 then
            return t
        end
    end
end

function parse_cookie(cookie)

    local i = 0
    local var = nil
    local val = nil
    local msg = ""
    local sig = nil

    for tok in string.gmatch(cookie, "[^|]+") do
        i = i + 1
        if i < 6 then
            msg = msg..tok.."|"
        end
        if i == 4 then
            var = extractkv(tok)
        end
        if i == 5 then
            val = extractkv(tok)
        end
        if i == 6 then
            sig = tok
        end
    end

    return var, val, msg, sig

end

function check_cookie_items(var, val, msg, sig, secret)
    
    local err = nil
    local ok = true

    if var ~= "user" then
        err = "No user variable"
        ok = false
        return ok, err 
    end

    if not val then
        err = "Value is nil"
        ok = false
        return ok, err
    end

    if not sig then
        err = "No Signature given"
        ok = false
        return ok, err
    end
    
    local encrypt = hmac.new(secret, "sha256")
    encrypt:update(msg)
    local exp_sig = tohex(encrypt:final())
    if exp_sig ~= sig then
        err = "Signature does not match"
        ok = false
        return ok, err
    end

    return ok, err
end


