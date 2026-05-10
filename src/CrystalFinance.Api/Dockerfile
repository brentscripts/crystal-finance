# Multi-stage build for C# Web API
# Stage 1: Build
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS builder

WORKDIR /src

# Copy solution and project files
COPY src/CrystalFinance.sln ./
COPY src/CrystalFinance.Api/CrystalFinance.Api.csproj ./CrystalFinance.Api/
COPY src/CrystalFinanceLibrary/CrystalFinanceLibrary.csproj ./CrystalFinanceLibrary/

# Restore dependencies
RUN dotnet restore CrystalFinance.Api/CrystalFinance.Api.csproj

# Copy application code
COPY src/CrystalFinance.Api/ ./CrystalFinance.Api/
COPY src/CrystalFinanceLibrary/ ./CrystalFinanceLibrary/

# Build and publish the application
RUN dotnet publish CrystalFinance.Api/CrystalFinance.Api.csproj -c Release -o /app/publish

# Stage 2: Runtime
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime

WORKDIR /app

# Install curl (Debian-based images)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy published application from builder
COPY --from=builder /app/publish .

# Expose API port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Set environment to production
ENV ASPNETCORE_ENVIRONMENT=Production
ENV ASPNETCORE_URLS=http://+:8080

# Run the application
ENTRYPOINT ["dotnet", "CrystalFinance.Api.dll"]
