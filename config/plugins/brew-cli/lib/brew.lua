local cmd = require("cmd")
local json = require("json")
local brew = {}

function brew.package(name)
    if name:sub(1, 5) == "cask/" then
        return "cask", name:sub(6)
    end
    return "formula", name
end

function brew.installed(kind)
    local output = cmd.exec('brew info --json=v2 --installed --"$BREW_KIND"', {
        env = { BREW_KIND = kind, HOMEBREW_NO_AUTO_UPDATE = "1" },
    })
    local info = json.decode(output)
    local installed = {}
    if kind == "formula" then
        for _, formula in ipairs(info.formulae) do
            local keg = formula.installed[1]
            if keg then
                installed[formula.full_name] = keg.version
                installed[formula.name] = keg.version
                for _, alias in ipairs(formula.aliases or {}) do
                    installed[alias] = keg.version
                end
            end
        end
    else
        for _, cask in ipairs(info.casks) do
            if type(cask.installed) == "string" then
                installed[cask.full_token] = cask.installed
                installed[cask.token] = cask.installed
            end
        end
    end
    return installed
end

function brew.apply(ctx, action)
    for _, pkg in ipairs(ctx.packages) do
        if ctx.dry_run then
            print("would " .. action .. " " .. pkg.name)
        else
            local kind, name = brew.package(pkg.name)
            print(action .. " " .. pkg.name)
            cmd.exec('brew "$BREW_ACTION" --"$BREW_KIND" -- "$BREW_PACKAGE"', {
                env = {
                    BREW_ACTION = action,
                    BREW_KIND = kind,
                    BREW_PACKAGE = name,
                },
            })
        end
    end
end

return brew
