function PLUGIN:PackageInstall(ctx)
    require("brew").apply(ctx, "install")
end
