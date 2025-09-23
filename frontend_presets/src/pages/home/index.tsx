// frontend/src/pages/home/index.tsx
import { ConditionalWrapper } from "../../components/ConditionalWrapper";
import TalkToVaani from "../../components/talk-to-vaani"
import Tryout from "../../components/home-tryout";

const Home = () => {
  return (
    <div className='home'>
      <section className="body">
        <ConditionalWrapper condition="call_test.tryout_component">
          <Tryout />
        </ConditionalWrapper>
        
        <ConditionalWrapper condition="call_test.talk_to_vaani_component">
          <TalkToVaani />
        </ConditionalWrapper>
      </section>
    </div>
  );
};

export default Home;