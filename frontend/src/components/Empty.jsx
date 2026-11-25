import Icon from "./Icon";

export default function Empty({
  icon = "leaf",
  title,
  children,
  headingLevel = 3,
}) {
  const Heading = `h${headingLevel}`;
  return (
    <div className="px-6 py-[55px] text-center">
      <span className="mb-5 inline-flex h-16 w-16 items-center justify-center rounded-[22px] bg-[#eaf0e5] text-[#6a8b6b]">
        <Icon name={icon} width="30" height="30" />
      </span>
      <Heading className={headingLevel === 3 ? "mb-2 font-[550]" : undefined}>
        {title}
      </Heading>
      <p className="mx-auto my-0 max-w-[360px] text-[0.9rem]">{children}</p>
    </div>
  );
}
