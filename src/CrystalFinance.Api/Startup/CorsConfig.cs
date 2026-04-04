namespace CrystalFinance.Api.Startup
{
    public static class CorsConfig
    {
        private const string PolicyName = "BlazorWasmPolicy";

        public static void AddCorsPolicy(this IServiceCollection services, IConfiguration config)
        {
            var uiUrl = config["UiBaseUrl"] ?? "https://localhost:7044";

            services.AddCors(options =>
            {
                options.AddPolicy(PolicyName, policy =>
                {
                    policy.WithOrigins(uiUrl)
                          .AllowAnyHeader()
                          .AllowAnyMethod()
                          .AllowCredentials(); // Essential for Entra ID
                });
            });
        }

        public static void UseCustomCors(this IApplicationBuilder app)
        {
            app.UseCors(PolicyName);
        }
    }
}
