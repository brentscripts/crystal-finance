using System.Text.Json.Serialization;

namespace CrystalFinanceLibrary.Models;

/// <summary>
/// Represents a paged result set with metadata about pagination.
/// </summary>
/// <typeparam name="T">The type of items in the result set.</typeparam>
public class PagedResult<T>
{
    /// <summary>
    /// Gets the items in the current page.
    /// </summary>
    [JsonPropertyName("items")]
    public List<T> Items { get; set; } = new();

    /// <summary>
    /// Gets the current page number (1-indexed).
    /// </summary>
    [JsonPropertyName("pageNumber")]
    public int PageNumber { get; set; }

    /// <summary>
    /// Gets the number of items per page.
    /// </summary>
    [JsonPropertyName("pageSize")]
    public int PageSize { get; set; }

    /// <summary>
    /// Gets the total number of items across all pages.
    /// </summary>
    [JsonPropertyName("totalItems")]
    public int TotalItems { get; set; }

    /// <summary>
    /// Gets the total number of pages.
    /// </summary>
    [JsonPropertyName("totalPages")]
    public int TotalPages => (TotalItems + PageSize - 1) / PageSize;

    /// <summary>
    /// Gets a value indicating whether there are more pages after the current one.
    /// </summary>
    [JsonPropertyName("hasNextPage")]
    public bool HasNextPage => PageNumber < TotalPages;

    /// <summary>
    /// Gets a value indicating whether there are pages before the current one.
    /// </summary>
    [JsonPropertyName("hasPreviousPage")]
    public bool HasPreviousPage => PageNumber > 1;
}
