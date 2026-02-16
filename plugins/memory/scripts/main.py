import asyncio
import json
import sys
from functools import wraps
from typing import Optional

import click

from lib import logging
from memory import (
    init_db,
    close_db,
    create_memory,
    get_memory,
    update_memory,
    delete_memory,
    search_memories,
    list_memories,
    get_memories_by_priority,
    set_priority,
    deprecate_memory,
    archive_memory,
    restore_memory,
    get_versions,
    get_version,
    rollback_to_version,
    diff_versions,
    add_relation,
    get_relations,
    remove_relation,
    RelationType,
    MemoryStatus,
    export_memories,
    import_memories,
    get_stats,
    clean_memories,
    create_session,
    end_session,
    record_error_solution,
    find_error_solution,
    mark_solution_success,
)


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return loop.run_until_complete(coro)


def with_debug(func):
    @wraps(func)
    @click.option("--debug", "debug_mode", is_flag=True, help="启用 DEBUG 模式")
    def wrapper(debug_mode: bool, *args, **kwargs):
        if debug_mode:
            logging.enable_debug()
        return func(*args, **kwargs)
    return wrapper


def with_db(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        async def _wrapper():
            await init_db()
            try:
                return await func(*args, **kwargs)
            finally:
                await close_db()
        return run_async(_wrapper())
    return wrapper


@click.group()
@click.pass_context
def main(ctx) -> None:
    pass


@main.command()
@click.argument("uri")
@with_debug
@with_db
async def read(uri: str) -> None:
    memory = await get_memory(uri)
    if not memory:
        click.echo(f"错误: 未找到记忆 {uri}", err=True)
        sys.exit(1)
    
    click.echo("=" * 60)
    click.echo(f"URI: {memory.uri}")
    click.echo(f"优先级: {memory.priority} | 状态: {memory.status}")
    click.echo(f"访问次数: {memory.access_count}")
    if memory.disclosure:
        click.echo(f"触发条件: {memory.disclosure}")
    click.echo("-" * 60)
    click.echo(memory.content)
    click.echo("=" * 60)


@main.command()
@click.argument("uri")
@click.argument("content")
@click.option("-p", "--priority", default=5, help="优先级 (0-10)")
@click.option("-d", "--disclosure", default="", help="触发条件")
@with_debug
@with_db
async def create(uri: str, content: str, priority: int, disclosure: str) -> None:
    memory = await create_memory(uri, content, priority, disclosure)
    click.echo(f"✓ 已创建记忆: {memory.uri}")
    click.echo(f"  ID: {memory.id} | 优先级: {memory.priority}")
    if disclosure:
        click.echo(f"  触发条件: {disclosure}")


@main.command()
@click.argument("uri")
@click.option("-c", "--content", help="新内容")
@click.option("-p", "--priority", type=int, help="新优先级")
@click.option("-d", "--disclosure", help="新触发条件")
@click.option("--append", is_flag=True, help="追加模式")
@click.option("--old", help="替换前文本")
@click.option("--new", "new_text", help="替换后文本")
@with_debug
@with_db
async def update(uri: str, content: Optional[str], priority: Optional[int], 
                 disclosure: Optional[str], append: bool, old: Optional[str], 
                 new_text: Optional[str]) -> None:
    memory = await update_memory(uri, content, priority, disclosure, append, old, new_text)
    if not memory:
        click.echo(f"错误: 未找到记忆 {uri}", err=True)
        sys.exit(1)
    
    click.echo(f"✓ 已更新记忆: {memory.uri}")


@main.command()
@click.argument("uri")
@click.option("--force", is_flag=True, help="硬删除（不可恢复）")
@with_debug
@with_db
async def delete(uri: str, force: bool) -> None:
    success = await delete_memory(uri, soft=not force)
    if not success:
        click.echo(f"错误: 未找到记忆 {uri}", err=True)
        sys.exit(1)
    
    action = "硬删除" if force else "软删除"
    click.echo(f"✓ 已{action}记忆: {uri}")


@main.command()
@click.argument("query")
@click.option("-d", "--domain", help="限定 URI 前缀")
@click.option("-l", "--limit", default=10, help="结果数量限制")
@click.option("--priority-min", type=int, help="最小优先级")
@click.option("--priority-max", type=int, help="最大优先级")
@with_debug
@with_db
async def search(query: str, domain: Optional[str], limit: int,
                 priority_min: Optional[int], priority_max: Optional[int]) -> None:
    uri_prefix = f"{domain}://" if domain else None
    memories = await search_memories(query, uri_prefix, priority_min, priority_max, limit=limit)
    
    if not memories:
        click.echo("未找到匹配的记忆")
        return
    
    click.echo("=" * 60)
    for i, mem in enumerate(memories, 1):
        stars = "⭐" * min(3, 11 - mem.priority)
        click.echo(f"\n{stars} [{i}] {mem.uri}")
        click.echo(f"   优先级: {mem.priority} | 访问: {mem.access_count}次")
        if mem.disclosure:
            click.echo(f"   触发: {mem.disclosure[:50]}...")
        preview = mem.content[:100] + "..." if len(mem.content) > 100 else mem.content
        click.echo(f"   摘要: {preview}")
    click.echo("\n" + "=" * 60)


@main.command("list")
@click.option("-d", "--domain", help="限定 URI 前缀")
@click.option("-l", "--limit", default=20, help="结果数量限制")
@click.option("--priority-min", type=int, help="最小优先级")
@click.option("--priority-max", type=int, help="最大优先级")
@click.option("--status", help="状态过滤")
@with_debug
@with_db
async def list_cmd(domain: Optional[str], limit: int,
                   priority_min: Optional[int], priority_max: Optional[int],
                   status: Optional[str]) -> None:
    uri_prefix = f"{domain}://" if domain else ""
    memories = await list_memories(uri_prefix, priority_min, priority_max, status, limit)
    
    if not memories:
        click.echo("没有找到记忆")
        return
    
    click.echo("=" * 60)
    for i, mem in enumerate(memories, 1):
        stars = "⭐" * min(3, 11 - mem.priority)
        click.echo(f"\n{stars} [{i}] {mem.uri}")
        click.echo(f"   优先级: {mem.priority} | 状态: {mem.status} | 访问: {mem.access_count}次")
        preview = mem.content[:80] + "..." if len(mem.content) > 80 else mem.content
        click.echo(f"   摘要: {preview}")
    click.echo("\n" + "=" * 60)


@main.command()
@click.argument("uri")
@click.argument("priority", type=int)
@with_debug
@with_db
async def priority(uri: str, priority: int) -> None:
    try:
        memory = await set_priority(uri, priority)
        if not memory:
            click.echo(f"错误: 未找到记忆 {uri}", err=True)
            sys.exit(1)
        click.echo(f"✓ 已设置优先级: {memory.uri} -> {priority}")
    except ValueError as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("uri")
@click.option("--reason", default="", help="废弃原因")
@with_debug
@with_db
async def deprecate(uri: str, reason: str) -> None:
    memory = await deprecate_memory(uri, reason)
    if not memory:
        click.echo(f"错误: 未找到记忆 {uri}", err=True)
        sys.exit(1)
    click.echo(f"✓ 已废弃记忆: {uri}")


@main.command()
@click.argument("uri")
@with_debug
@with_db
async def archive(uri: str) -> None:
    memory = await archive_memory(uri)
    if not memory:
        click.echo(f"错误: 未找到记忆 {uri}", err=True)
        sys.exit(1)
    click.echo(f"✓ 已归档记忆: {uri}")


@main.command()
@click.argument("uri")
@with_debug
@with_db
async def restore(uri: str) -> None:
    memory = await restore_memory(uri)
    if not memory:
        click.echo(f"错误: 未找到记忆 {uri}", err=True)
        sys.exit(1)
    click.echo(f"✓ 已恢复记忆: {uri}")


@main.command()
@click.argument("uri")
@click.option("-l", "--limit", default=10, help="版本数量限制")
@with_debug
@with_db
async def versions(uri: str, limit: int) -> None:
    versions = await get_versions(uri, limit)
    
    if not versions:
        click.echo(f"记忆 {uri} 没有历史版本")
        return
    
    click.echo("=" * 60)
    click.echo(f"记忆: {uri}")
    click.echo("-" * 60)
    for v in versions:
        click.echo(f"\n版本 {v.version} | {v.changed_at}")
        click.echo(f"  原因: {v.change_reason or '无'} | 来源: {v.changed_by}")
        preview = v.content[:100] + "..." if len(v.content) > 100 else v.content
        click.echo(f"  内容: {preview}")
    click.echo("=" * 60)


@main.command()
@click.argument("uri")
@click.argument("version", type=int)
@with_debug
@with_db
async def rollback(uri: str, version: int) -> None:
    memory = await rollback_to_version(uri, version)
    if not memory:
        click.echo(f"错误: 无法回滚到版本 {version}", err=True)
        sys.exit(1)
    click.echo(f"✓ 已回滚记忆 {uri} 到版本 {version}")


@main.command()
@click.argument("uri")
@click.argument("version1", type=int)
@click.argument("version2", type=int)
@with_debug
@with_db
async def diff(uri: str, version1: int, version2: int) -> None:
    result = await diff_versions(uri, version1, version2)
    if not result:
        click.echo(f"错误: 无法获取版本差异", err=True)
        sys.exit(1)
    
    content1, content2 = result
    click.echo("=" * 60)
    click.echo(f"版本 {version1}:")
    click.echo("-" * 60)
    click.echo(content1[:500])
    click.echo("=" * 60)
    click.echo(f"版本 {version2}:")
    click.echo("-" * 60)
    click.echo(content2[:500])
    click.echo("=" * 60)


@main.command()
@click.argument("source_uri")
@click.argument("target_uri")
@click.argument("relation_type", type=click.Choice(["relates_to", "depends_on", "contradicts", "evolves_from"]))
@click.option("-s", "--strength", type=float, default=0.5, help="关系强度 (0-1)")
@with_debug
@with_db
async def relate(source_uri: str, target_uri: str, relation_type: str, strength: float) -> None:
    rel_type = RelationType(relation_type)
    relation = await add_relation(source_uri, target_uri, rel_type, strength)
    if not relation:
        click.echo(f"错误: 无法创建关系", err=True)
        sys.exit(1)
    click.echo(f"✓ 已创建关系: {source_uri} --[{relation_type}]--> {target_uri}")


@main.command()
@click.argument("uri")
@click.option("-d", "--direction", type=click.Choice(["in", "out", "both"]), default="both", help="关系方向")
@with_debug
@with_db
async def relations(uri: str, direction: str) -> None:
    relations = await get_relations(uri, direction)
    
    if not relations:
        click.echo(f"记忆 {uri} 没有关系")
        return
    
    click.echo("=" * 60)
    click.echo(f"记忆: {uri}")
    click.echo("-" * 60)
    for rel in relations:
        if rel["direction"] == "out":
            click.echo(f"  → [{rel['relation_type']}] {rel['target_uri']} (强度: {rel['strength']})")
        else:
            click.echo(f"  ← [{rel['relation_type']}] {rel['source_uri']} (强度: {rel['strength']})")
    click.echo("=" * 60)


@main.command()
@click.argument("output", type=click.Path())
@click.option("-d", "--domain", help="限定 URI 前缀")
@click.option("--include-versions", is_flag=True, help="包含版本历史")
@click.option("--include-relations", is_flag=True, help="包含关系")
@with_debug
@with_db
async def export(output: str, domain: Optional[str], include_versions: bool, include_relations: bool) -> None:
    uri_prefix = f"{domain}://" if domain else None
    data = await export_memories(uri_prefix, include_versions, include_relations)
    
    with open(output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    click.echo(f"✓ 已导出 {len(data['memories'])} 条记忆到 {output}")


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--strategy", type=click.Choice(["skip", "overwrite", "merge"]), default="skip", help="导入策略")
@with_debug
@with_db
async def import_cmd(input_file: str, strategy: str) -> None:
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    stats = await import_memories(data, strategy)
    
    click.echo(f"✓ 导入完成:")
    click.echo(f"  创建: {stats['created']}")
    click.echo(f"  更新: {stats['updated']}")
    click.echo(f"  跳过: {stats['skipped']}")
    click.echo(f"  错误: {stats['errors']}")


@main.command()
@click.option("--unused-days", type=int, help="清理未访问天数")
@click.option("--deprecated-days", type=int, help="清理已废弃天数")
@click.option("--dry-run", is_flag=True, help="仅预览，不执行")
@with_debug
@with_db
async def clean(unused_days: Optional[int], deprecated_days: Optional[int], dry_run: bool) -> None:
    stats = await clean_memories(unused_days, deprecated_days, dry_run)
    
    if dry_run:
        click.echo("预览模式 - 以下是将执行的操作:")
    click.echo(f"  将归档: {stats['archived']}")
    click.echo(f"  将清理: {stats['cleaned']}")


@main.command()
@with_debug
@with_db
async def stats() -> None:
    stats = await get_stats()
    
    click.echo("=" * 60)
    click.echo("记忆统计")
    click.echo("=" * 60)
    click.echo(f"\n总数: {stats['total']}")
    click.echo(f"  活跃: {stats['active']}")
    click.echo(f"  已废弃: {stats['deprecated']}")
    click.echo(f"  已归档: {stats['archived']}")
    
    if stats['by_priority']:
        click.echo("\n按优先级分布:")
        for p, count in sorted(stats['by_priority'].items()):
            click.echo(f"  优先级 {p}: {count}")
    
    if stats['by_uri_prefix']:
        click.echo("\n按 URI 前缀分布:")
        for prefix, count in sorted(stats['by_uri_prefix'].items(), key=lambda x: -x[1]):
            click.echo(f"  {prefix}://: {count}")
    
    click.echo(f"\n版本总数: {stats['versions_count']}")
    click.echo(f"关系总数: {stats['relations_count']}")
    click.echo("=" * 60)


@main.command()
@click.argument("uri")
@click.option("-l", "--limit", default=5, help="预加载数量")
@with_debug
@with_db
async def preload(uri: str, limit: int) -> None:
    memories = await get_memories_by_priority(limit)
    
    if not memories:
        click.echo("没有需要预加载的记忆")
        return
    
    click.echo("=" * 60)
    click.echo("预加载记忆:")
    click.echo("-" * 60)
    for mem in memories:
        click.echo(f"\n[{mem.priority}] {mem.uri}")
        if mem.disclosure:
            click.echo(f"触发: {mem.disclosure}")
        click.echo(mem.content[:200])
    click.echo("=" * 60)


@main.command()
@with_debug
def hooks() -> None:
    from hooks import handle_hook
    handle_hook()


@main.command()
@click.option("-p", "--port", type=int, default=None, help="端口号（默认自动查找可用端口）")
@click.option("--no-browser", is_flag=True, help="不自动打开浏览器")
@with_debug
def web(port: Optional[int], no_browser: bool) -> None:
    """启动 Web 管理界面"""
    from web import start_web
    start_web(port=port, open_browser=not no_browser)


if __name__ == "__main__":
    main()
